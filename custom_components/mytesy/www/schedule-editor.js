/* MyTESY visual weekly schedule editor. Service calls use the signed-in HA session. */
const DAYS=['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'];
const escapeHTML = x => String(x ?? '').replace(/[&<>"']/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
class TesySchedulePanel extends HTMLElement {
  constructor(){super();this.attachShadow({mode:'open'});this._busy=false;this._message='';this._editing=null;}
  set hass(value){this._hass=value;this.draw();}
  get hass(){return this._hass;}
  connectedCallback(){this.draw();}
  get mac(){return new URLSearchParams(location.search).get('mac') || '';}
  get source(){return Object.entries(this._hass?.states || {}).find(([,s])=>{const a=s.attributes;if(!a?.mytesy_schedule_editor || typeof a.editor_url!=='string')return false;try{return new URL(a.editor_url,location.origin).searchParams.get('mac')===this.mac;}catch{return false;}})?.[1];}
  get intervals(){return this.source?.attributes?.program_intervals || [];}
  get scheduleReported(){return this.source?.attributes?.program_data_available === true;}
  draw(){
    if (!this.isConnected || !this._hass) return;
    const source=this.source, entries=this.intervals;
    const currentDay=this._editing?.day || 1;

    this.shadowRoot.innerHTML=`<style>
      :host{display:block;background:var(--primary-background-color);color:var(--primary-text-color);min-height:100vh;font-family:var(--paper-font-body1_-_font-family,Arial,sans-serif)}
      main{max-width:1400px;margin:auto;padding:24px 18px 65px}.layout{display:grid;grid-template-columns:250px minmax(0,1fr);gap:20px;margin-top:18px}.side{align-self:start;position:sticky;top:18px}.side section{margin-top:0}.content{min-width:0}.toggle{position:relative;display:inline-flex;align-items:center;width:56px;height:30px;flex:none}.toggle input{opacity:0;position:absolute;width:100%;height:100%;margin:0;cursor:pointer;z-index:2}.track{display:block;width:56px;height:30px;border-radius:30px;background:var(--disabled-text-color,#aaa);transition:background .2s}.track:before{content:"";display:block;width:24px;height:24px;border-radius:50%;margin:3px;background:white;box-shadow:0 1px 3px #0003;transition:transform .2s}.toggle input:checked+.track{background:var(--success-color,#39a36a)}.toggle input:checked+.track:before{transform:translateX(26px)}.toggle input:disabled{cursor:wait}.toggleRow{display:flex;align-items:center;justify-content:space-between;gap:12px;margin:18px 0}.status{font-size:13px;color:var(--secondary-text-color)}header{display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px}
      h1{font-size:28px;margin:0}p{color:var(--secondary-text-color)}section{background:var(--card-background-color,#fff);border:1px solid var(--divider-color,#ddd);border-radius:18px;padding:18px;margin-top:18px}
      .days{display:grid;grid-template-columns:repeat(7,minmax(0,1fr));gap:10px;margin-top:16px}.day{border:1px solid var(--divider-color,#aaa);border-radius:12px;padding:12px;min-height:180px}
      .title{font-weight:700;margin-bottom:14px}.event{background:var(--secondary-background-color,#e8f0f8);padding:8px;border-radius:9px;margin:6px 0;font-size:13px;overflow-wrap:anywhere}
      button{padding:9px 14px;border-radius:9px;background:var(--primary-color,#1976d2);color:white;border:0;cursor:pointer}button.secondary{background:var(--secondary-background-color,#ddd);color:var(--primary-text-color)}button.danger{background:#a33239}button:disabled{opacity:.5}
      form{display:flex;gap:12px;align-items:end;flex-wrap:wrap}label{display:grid;gap:6px;font-size:13px}input,select{padding:9px;background:var(--card-background-color,#fff);color:var(--primary-text-color);border:1px solid var(--divider-color,#999);border-radius:8px}
      .actions{display:flex;gap:8px;margin-top:9px}small{color:var(--secondary-text-color)}.notice{padding:10px;border-radius:8px;background:var(--secondary-background-color,#eee)}
      @media(max-width:950px){.layout{grid-template-columns:1fr}.side{position:static}.days{grid-template-columns:repeat(2,1fr)}}@media(max-width:500px){.days{grid-template-columns:1fr}}
    </style><main><header><div><h1>TESY weekly schedules</h1><p>${escapeHTML(this.mac)} · ${source?'Connected to Home Assistant':'Device not found'}</p></div><button class="secondary" id="back">Back to Home Assistant</button></header>
    <div class="layout"><aside class="side"><section><h2>${escapeHTML(source?.attributes?.device_name || "Heater")}</h2><small>Weekly program editor</small><p class="status">Schedule availability: ${this.scheduleReported ? "Reported by TESY" : "Not reported by TESY"}</p></section></aside><div class="content">
    <section><b>Weekly program status:</b> ${escapeHTML(source?.attributes?.program_status_display || "Status unavailable")}
    ${!this.scheduleReported ? `<p class="notice">TESY has not provided schedule intervals. This does not mean the timetable is empty. Editing and deleting are disabled until TESY reports its schedule.</p>` : `<p>Intervals repeat weekly. Changes are sent to TESY via Home Assistant actions.</p>`}
    ${this._message?`<div class="notice">${escapeHTML(this._message)}</div>`:''}</section>
    <section><h2>Weekly timetable</h2><div class="days">${DAYS.map((day,i)=>`<div class="day"><div class="title">${day}</div>${entries.filter(e=>Number(e.day)===i+1).sort((a,b)=>String(a.from).localeCompare(String(b.from))).map(e=>`<div class="event"><b>${escapeHTML(e.from)}–${escapeHTML(e.to)}</b><div>${escapeHTML(e.temp)} °C</div><div class="actions"><button class="secondary edit" data-id="${escapeHTML(e.program_number)}">Edit</button><button class="danger delete" data-id="${escapeHTML(e.program_number)}">Delete</button></div></div>`).join('')||(this.scheduleReported?'<small>No intervals</small>':'<small>Schedule not reported</small>')}</div>`).join('')}</div></section>
    <section><h2>${this._editing?'Edit interval':'Add interval'}</h2><form id="interval"><label>Day<select name="day">${DAYS.map((d,i)=>`<option value="${i+1}" ${Number(this._editing?.day||currentDay)===i+1?'selected':''}>${d}</option>`).join('')}</select></label><label>From<input name="from" type="time" value="${escapeHTML(this._editing?.from||'08:00')}" required></label><label>To<input name="to" type="time" value="${escapeHTML(this._editing?.to||'10:00')}" required></label><label>Temperature °C<input name="temp" type="number" min="5" max="35" step="1" value="${escapeHTML(this._editing?.temp??22)}" required></label><button type="submit" ${this._busy || !this.scheduleReported?'disabled':''}>${this._editing?'Save changes':'Add interval'}</button>${this._editing?'<button class="secondary" type="button" id="cancel">Cancel</button>':''}</form></section></div></div></main>`;
    const root=this.shadowRoot;root.getElementById('back').onclick=()=>location.assign('/');
    root.getElementById('cancel')?.addEventListener('click',()=>{this._editing=null;this.draw();});
    root.querySelectorAll('.edit').forEach(b=>b.onclick=()=>{this._editing=entries.find(e=>String(e.program_number)===b.dataset.id);this.draw();});
    root.querySelectorAll('.delete').forEach(b=>b.onclick=async()=>{const item=entries.find(e=>String(e.program_number)===b.dataset.id);if(!item||!this.scheduleReported||!confirm('Delete this interval on the TESY heater?'))return;await this.call('delete_program_interval',{mac:this.mac,program_number:Number(item.program_number)});});
    root.getElementById('interval').onsubmit=async e=>{e.preventDefault();const data=Object.fromEntries(new FormData(e.currentTarget));if(!this.scheduleReported){this._message='Cannot edit: TESY has not reported the current schedule.';this.draw();return;}if(data.to<=data.from){this._message='End time must be later than start time';this.draw();return;}
      const used=new Set(entries.map(x=>Number(x.program_number)));const num=this._editing?.program_number || Array.from({length:255},(_,i)=>i+1).find(n=>!used.has(n));
      if(!num){this._message='No free schedule slots';this.draw();return;}
      await this.call('set_program_interval',{mac:this.mac,day:Number(data.day),from:data.from,to:data.to,temp:Number(data.temp),program_number:Number(num)});
    };
  }
  async call(service,data){this._busy=true;this._message='Sending change to TESY…';this.draw();try{await this._hass.callService('mytesy',service,data);this._message='Command sent. Waiting for cloud state to reflect the change.';this._editing=null;}catch(e){this._message='TESY rejected change: '+String(e.message||e);}finally{this._busy=false;this.draw();}}
}
if (!customElements.get('mytesy-schedule-panel-1-2-12')) customElements.define('mytesy-schedule-panel-1-2-12',TesySchedulePanel);
