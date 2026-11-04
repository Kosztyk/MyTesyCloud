"""Regression checks for Frenck's multi-account, lifecycle and reauth findings.

Use isolated AST-loaded functions so CI can run without a full HA installation.
"""
import ast
import asyncio
import json
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
COMP = ROOT / 'custom_components' / 'mytesy'


def functions(file, names, env):
    tree = ast.parse((COMP / file).read_text())
    nodes = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name in names]
    module = ast.Module(body=nodes, type_ignores=[])
    exec(compile(module, str(COMP / file), 'exec'), env)
    return env


class RecordsAndServices(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.records = {}
        self.entries = [SimpleNamespace(entry_id='account-a'), SimpleNamespace(entry_id='account-b')]
        self.commands = []
        self.refreshed = []
        self.group_calls = []
        self.handlers = {}

        class Services:
            def has_service(_, domain, name):
                return (domain, name) in self.handlers
            def async_register(_, domain, name, fn, schema=None):
                self.handlers[domain, name] = fn
            def async_remove(_, domain, name):
                self.handlers.pop((domain, name), None)
        self.hass = SimpleNamespace(
            data={'mytesy': {'_editor': {'visible': True}}},
            services=Services(),
            config_entries=SimpleNamespace(async_entries=lambda domain: list(self.entries)),
        )
        class FakeSchema:
            def __getattr__(self, name):
                return lambda *args, **kwargs: args[0] if args else None
        vol = FakeSchema()
        vol.Schema = lambda x: x
        cv = SimpleNamespace(string=str)
        class HomeAssistantError(Exception):
            pass
        env = {
            'HomeAssistant': object, 'ServiceCall': object, 'DOMAIN': 'mytesy',
            'SERVICE_RESET_HISTORY': 'reset_history', 'HomeAssistantError': HomeAssistantError,
            'vol': vol, 'cv': cv,
        }
        self.env = functions('__init__.py', ['_entry_records', '_resolve_record', '_resolve_device', '_register_services'], env)
        async def command(account, device, action, params):
            self.commands.append((account, device['mac'], action, params))
        async def group(account, endpoint, payload):
            self.group_calls.append((account, endpoint, payload))
        async def refresh(account):
            self.refreshed.append(account)
        async def reset(account, mac):
            self.refreshed.append((account, mac, 'reset'))
        for account, mac in [('account-a', 'AA:11'), ('account-b', 'BB:22')]:
            self.hass.data['mytesy'][account] = {
                'coordinator': SimpleNamespace(data={mac: {'device': {'mac': mac}}},
                                               async_request_refresh=lambda account=account: refresh(account)),
                'api': SimpleNamespace(
                    async_send_command=lambda dev, action, params, account=account: command(account, dev, action, params),
                    async_group_request=lambda endpoint, payload, account=account: group(account, endpoint, payload)),
                'history': SimpleNamespace(async_reset=lambda mac, account=account: reset(account, mac)),
            }
        self.env['_register_services'](self.hass)

    async def test_editor_is_never_treated_as_account(self):
        self.assertEqual(set(self.env['_entry_records'](self.hass)), {'account-a', 'account-b'})
        record, payload = self.env['_resolve_device'](self.hass, 'BB:22')
        self.assertEqual(payload['device']['mac'], 'BB:22')

    async def test_schedule_services_route_to_correct_second_account(self):
        await self.handlers['mytesy', 'set_program_interval'](SimpleNamespace(data={
            'mac': 'BB:22', 'day': 1, 'from': '09:00', 'to': '10:00', 'temp': 22, 'program_number': 2,
        }))
        await self.handlers['mytesy', 'delete_program_interval'](SimpleNamespace(data={
            'mac': 'AA:11', 'program_number': 2,
        }))
        self.assertEqual([x[:3] for x in self.commands], [
            ('account-b', 'BB:22', 'setProgram'), ('account-a', 'AA:11', 'deleteProgram'),
        ])

    async def test_group_requires_explicit_account_when_multiple_loaded(self):
        with self.assertRaises(self.env['HomeAssistantError']):
            await self.handlers['mytesy', 'manage_group'](SimpleNamespace(data={
                'operation': 'create', 'name': 'Garage',
            }))
        await self.handlers['mytesy', 'manage_group'](SimpleNamespace(data={
            'operation': 'create', 'name': 'Garage', 'entry_id': 'account-b',
        }))
        self.assertEqual(self.group_calls, [('account-b', 'create-group', {'name': 'Garage'})])

    async def test_duplicate_device_requires_explicit_account(self):
        self.hass.data['mytesy']['account-b']['coordinator'].data['AA:11'] = {'device': {'mac': 'AA:11'}}
        with self.assertRaisesRegex(self.env['HomeAssistantError'], 'multiple accounts'):
            self.env['_resolve_device'](self.hass, 'AA:11')
        rec, device = self.env['_resolve_device'](self.hass, 'AA:11', 'account-b')
        self.assertEqual(device['device']['mac'], 'AA:11')

    async def test_global_services_register_only_once(self):
        before = dict(self.handlers)
        self.env['_register_services'](self.hass)
        self.assertEqual(self.handlers, before)


class AuthFlow(unittest.IsolatedAsyncioTestCase):
    async def test_auth_exception_is_reauth_trigger_not_poll_retry(self):
        source = (COMP / 'coordinator.py').read_text()
        self.assertLess(source.index('except TesyCloudAuthError as err:'), source.index('except TesyCloudError as err:'))
        self.assertIn('raise ConfigEntryAuthFailed(', source)
        self.assertIn('raise UpdateFailed(', source)

    async def test_reauth_flow_requires_password_and_updates_existing_entry(self):
        source = (COMP / 'config_flow.py').read_text()
        tree = ast.parse(source)
        flow = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'TesyCloudConfigFlow')
        methods = {n.name: n for n in flow.body if isinstance(n, ast.AsyncFunctionDef)}
        self.assertIn('async_step_reauth', methods)
        self.assertIn('async_step_reauth_confirm', methods)
        method = ast.unparse(methods['async_step_reauth_confirm'])
        self.assertIn('self._get_reauth_entry()', method)
        self.assertIn('self.async_update_reload_and_abort(', method)
        self.assertIn('CONF_PASSWORD', method)
        # New credentials must actually reach the authentication endpoint.
        self.assertIn("user_id=", method)
        fields = json.loads((COMP/'translations/en.json').read_text())
        self.assertIn('reauth_confirm', fields['config']['step'])
        self.assertEqual(fields, json.loads((COMP/'strings.json').read_text()))

    async def test_transient_auth_network_failure_not_classified_bad_password(self):
        source = (COMP/'api.py').read_text()
        self.assertIn('raise TesyCloudError("Cannot reach MyTESY authentication service")', source)
        self.assertIn('if response.status in (401, 403):', source)
        self.assertIn('if resp.status in (401, 403):', source)


class HardwareAndEnergy(unittest.TestCase):
    def test_all_existing_write_features_remain_available(self):
        switches = (COMP/'switch.py').read_text()
        numbers = (COMP/'number.py').read_text()
        calendar = (COMP/'calendar.py').read_text()
        water_heater = (COMP/'water_heater.py').read_text()
        setup = (COMP/'__init__.py').read_text()
        for cmd in ('setAdaptiveStart', 'setAntiFrost', 'setOpenedWindow', 'setLockDevice', 'setUV', 'setProgramStatus'):
            self.assertIn(cmd, switches)
        for cmd in ('setComfortTemp', 'setEcoTemp', 'setTCorrection'):
            self.assertIn(cmd, numbers)
        for cmd in ('setProgram', 'deleteProgram'):
            self.assertIn(cmd, calendar)
            self.assertIn(cmd, setup)
        for cmd in ('powerOnOff', 'setStandby', 'setMode'):
            self.assertIn(cmd, water_heater)

    def test_energy_compatibility_is_unchanged(self):
        sensor = (COMP/'sensor.py').read_text()
        self.assertIn('_energy_estimated', sensor)
        self.assertIn('SensorStateClass.TOTAL_INCREASING', sensor)

    def test_global_cleanup_covers_all_services_and_editor(self):
        setup = (COMP/'__init__.py').read_text()
        self.assertIn('await async_unload_editor(hass)', setup)
        self.assertIn('"delete_program_interval", "manage_group"', setup)
        self.assertNotIn('for record in hass.data.get(DOMAIN, {}).values()', setup)

if __name__ == '__main__':
    unittest.main()
