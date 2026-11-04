/* Open TESY schedule editor when its sensor is tapped. */
if (globalThis.window && !window.__mytesyScheduleOpenInstalled) {
  window.__mytesyScheduleOpenInstalled = true;
  window.addEventListener('hass-more-info', event => {
    if (event.detail?.view || event.detail?.tab) return;
    const entityId = event.detail?.entityId;
    if (!entityId?.startsWith('sensor.')) return;
    const host = event.composedPath().find(x => x?.hass) || document.querySelector('home-assistant');
    const attrs = host?.hass?.states?.[entityId]?.attributes;
    if (attrs?.mytesy_schedule_editor !== true || typeof attrs.editor_url !== 'string') return;
    const url = new URL(attrs.editor_url, window.location.origin);
    if (url.origin !== window.location.origin || url.pathname !== '/mytesy-schedules' || !url.searchParams.get('mac')) return;
    event.stopImmediatePropagation();
    window.location.assign(url.pathname + url.search);
  }, true);
}
