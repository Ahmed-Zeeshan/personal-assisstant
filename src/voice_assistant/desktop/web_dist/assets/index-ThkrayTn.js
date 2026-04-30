(function(){const e=document.createElement("link").relList;if(e&&e.supports&&e.supports("modulepreload"))return;for(const s of document.querySelectorAll('link[rel="modulepreload"]'))i(s);new MutationObserver(s=>{for(const r of s)if(r.type==="childList")for(const l of r.addedNodes)l.tagName==="LINK"&&l.rel==="modulepreload"&&i(l)}).observe(document,{childList:!0,subtree:!0});function t(s){const r={};return s.integrity&&(r.integrity=s.integrity),s.referrerPolicy&&(r.referrerPolicy=s.referrerPolicy),s.crossOrigin==="use-credentials"?r.credentials="include":s.crossOrigin==="anonymous"?r.credentials="omit":r.credentials="same-origin",r}function i(s){if(s.ep)return;s.ep=!0;const r=t(s);fetch(s.href,r)}})();class S{el;constructor(e){this.el=document.createElement("header"),this.el.className="h-12 px-5 flex items-center justify-between border-b border-border bg-surface/40",this.el.innerHTML=`
      <div class="flex items-center gap-3">
        <span class="font-mono text-sm">voice-assistant</span>
        <span class="text-dim text-xs">·</span>
        <span data-status class="text-xs text-muted">idle</span>
      </div>
      <button data-settings aria-label="Settings"
        class="h-9 w-9 grid place-items-center rounded-md hover:bg-bg/40 transition-colors text-muted hover:text-fg">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
          <circle cx="12" cy="12" r="3"/>
          <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>
        </svg>
      </button>
    `,e.appendChild(this.el)}setStatus(e){const t=this.el.querySelector("[data-status]");t&&(t.textContent=e)}onSettingsClick(e){this.el.querySelector("[data-settings]").addEventListener("click",e)}}class k{el;canvas;ctx;state="idle";rms=0;rafId=null;startTime=performance.now();constructor(e){this.el=document.createElement("div"),this.el.className="flex-1 grid place-items-center relative",this.el.innerHTML=`
      <div class="absolute inset-0 pointer-events-none"
        style="background: radial-gradient(closest-side, rgba(149,128,255,0.10), transparent 60%); filter: blur(60px);"></div>
      <canvas data-orb width="384" height="384" class="relative"></canvas>
      <p data-hint class="absolute bottom-12 text-sm text-muted">Press the hotkey to talk</p>
    `,e.appendChild(this.el),this.canvas=this.el.querySelector("[data-orb]");const t=this.canvas.getContext("2d");if(!t)throw new Error("canvas 2d context unavailable");this.ctx=t,this.loop()}setState(e){this.state=e;const t=this.el.querySelector("[data-hint]");t&&(t.textContent={idle:"Press the hotkey to talk",listening:"Listening…",thinking:"Thinking…",speaking:"Speaking…",error:"Something went wrong."}[e])}setRms(e){this.rms=Math.max(0,Math.min(1,e))}loop=()=>{const e=(performance.now()-this.startTime)/1e3,t=this.canvas.width,i=this.canvas.height;this.ctx.clearRect(0,0,t,i);const s=t/2,r=i/2,l="rgba(149,128,255,";let o=90+Math.sin(e*1.2)*4;this.state==="listening"&&(o=90+60*this.rms),this.state==="speaking"&&(o=90+Math.sin(e*6)*12),this.state==="thinking"&&(o=90);const n=this.ctx.createRadialGradient(s,r,o*.4,s,r,o*1.6);n.addColorStop(0,l+"0.50)"),n.addColorStop(1,l+"0)"),this.ctx.fillStyle=n,this.ctx.beginPath(),this.ctx.arc(s,r,o*1.6,0,Math.PI*2),this.ctx.fill();const h=this.ctx.createRadialGradient(s,r,0,s,r,o);if(h.addColorStop(0,l+"0.95)"),h.addColorStop(1,l+"0.45)"),this.ctx.fillStyle=h,this.ctx.beginPath(),this.ctx.arc(s,r,o,0,Math.PI*2),this.ctx.fill(),this.state==="thinking"){this.ctx.strokeStyle="#e6e8eb",this.ctx.lineWidth=3,this.ctx.lineCap="round",this.ctx.beginPath();const m=e*2%(Math.PI*2);this.ctx.arc(s,r,o+16,m,m+Math.PI*.6),this.ctx.stroke()}this.state==="error"&&(this.ctx.fillStyle=`rgba(245,158,11,${.4+.3*Math.sin(e*8)})`,this.ctx.beginPath(),this.ctx.arc(s,r,o,0,Math.PI*2),this.ctx.fill()),this.rafId=requestAnimationFrame(this.loop)};destroy(){this.rafId!==null&&cancelAnimationFrame(this.rafId)}}class C{el;streamingLine=null;constructor(e){this.el=document.createElement("section"),this.el.className="flex-1 overflow-y-auto px-5 py-4 space-y-3",this.el.innerHTML='<p class="text-dim text-sm">Press the hotkey or type a command to start.</p>',e.appendChild(this.el)}push(e){this.el.querySelector("p.text-dim")&&this.el.replaceChildren();const t=document.createElement("div");t.className="flex gap-3";const i=e.speaker==="user"?'<span class="text-xs text-dim shrink-0 mt-0.5 w-16">you</span>':'<span class="text-xs text-accent shrink-0 mt-0.5 w-16">assistant</span>',s=document.createElement("p");if(s.className="text-sm leading-6 text-fg",s.textContent=e.text,t.innerHTML=i,t.appendChild(s),e.tool_call){const r=document.createElement("pre");r.className="text-xs text-muted font-mono ml-19 mt-1",r.textContent=`↳ ${e.tool_call}`,t.appendChild(r)}this.el.appendChild(t),this.el.scrollTop=this.el.scrollHeight}startAssistant(){this.el.querySelector("p.text-dim")&&this.el.replaceChildren();const e=document.createElement("div");e.className="flex gap-3",e.innerHTML='<span class="text-xs text-accent shrink-0 mt-0.5 w-16">assistant</span>';const t=document.createElement("p");t.className="text-sm leading-6 text-fg",t.textContent="",e.appendChild(t),this.el.appendChild(e),this.streamingLine=t,this.el.scrollTop=this.el.scrollHeight}appendAssistant(e){this.streamingLine||this.startAssistant(),this.streamingLine.textContent=(this.streamingLine.textContent||"")+e,this.el.scrollTop=this.el.scrollHeight}endAssistant(){this.streamingLine=null}}class _{el;input;submitHandler=()=>{};recordHandler=()=>{};constructor(e){this.el=document.createElement("footer"),this.el.className="p-4 border-t border-border bg-surface/40 flex gap-2",this.el.innerHTML=`
      <button data-record aria-label="Hold to record"
        class="h-11 w-11 shrink-0 grid place-items-center rounded-md border border-border bg-surface hover:border-accent/40 transition-colors">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
          <rect x="9" y="2" width="6" height="12" rx="3"/>
          <path d="M5 10v2a7 7 0 0 0 14 0v-2"/>
          <line x1="12" y1="19" x2="12" y2="22"/>
        </svg>
      </button>
      <input data-input type="text" placeholder="Type a command..."
        class="flex-1 h-11 px-4 rounded-md border border-border bg-bg text-fg placeholder:text-dim focus:outline-none focus:border-accent" />
    `,e.appendChild(this.el),this.input=this.el.querySelector("[data-input]"),this.input.addEventListener("keydown",t=>{t.key==="Enter"&&this.input.value.trim()&&(this.submitHandler(this.input.value.trim()),this.input.value="")}),this.el.querySelector("[data-record]").addEventListener("click",()=>this.recordHandler())}onSubmit(e){this.submitHandler=e}onRecord(e){this.recordHandler=e}}class L{el;saveHandler=async()=>({ok:!0});currentCfg=null;constructor(e){this.el=document.createElement("aside"),this.el.className="fixed inset-y-0 right-0 w-full max-w-md bg-surface border-l border-border translate-x-full transition-transform duration-200 ease-out z-30 flex flex-col",this.el.innerHTML=`
      <header class="h-12 px-5 flex items-center justify-between border-b border-border">
        <h2 class="font-semibold">Settings</h2>
        <button data-close class="h-9 w-9 grid place-items-center rounded-md hover:bg-bg/40 text-muted hover:text-fg">×</button>
      </header>
      <form data-form class="flex-1 overflow-y-auto p-5 space-y-5 text-sm">
        <div>
          <label class="block text-muted mb-1">Provider</label>
          <select data-field="provider" class="w-full h-10 px-3 rounded-md border border-border bg-bg text-fg">
            <option value="anthropic">Anthropic Claude</option>
            <option value="openai">OpenAI GPT</option>
            <option value="gemini">Google Gemini</option>
            <option value="ollama">Ollama (local)</option>
          </select>
        </div>
        <div>
          <label class="block text-muted mb-1">Model</label>
          <select data-field="model" class="w-full h-10 px-3 rounded-md border border-border bg-bg text-fg"></select>
        </div>
        <div data-secret-row>
          <label class="flex items-center justify-between text-muted mb-1">
            <span data-secret-label>API key</span>
            <span data-saved-badge class="hidden text-success text-xs font-medium">✓ saved</span>
          </label>
          <div class="relative">
            <input data-field="secret" type="password" class="w-full h-10 px-3 pr-12 rounded-md border border-border bg-bg text-fg" placeholder="sk-…" />
            <button type="button" data-toggle-secret aria-label="Show or hide key"
              class="absolute right-1 top-1 h-8 w-10 grid place-items-center rounded text-dim hover:text-fg hover:bg-surface">
              <svg data-eye-show width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
              <svg data-eye-hide class="hidden" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>
            </button>
          </div>
          <p class="text-xs text-dim mt-1" data-secret-hint>Stored in ~/.voice-assistant/.env, mode 0600.</p>
        </div>
        <div>
          <label class="block text-muted mb-1">Hotkey</label>
          <input data-field="hotkey" class="w-full h-10 px-3 rounded-md border border-border bg-bg text-fg" placeholder="ctrl+shift+space" />
        </div>
        <div>
          <label class="block text-muted mb-1">Allowed folders (comma-separated)</label>
          <input data-field="roots" class="w-full h-10 px-3 rounded-md border border-border bg-bg text-fg" placeholder="~" />
        </div>
        <div class="border-t border-border pt-5 space-y-3">
          <h3 class="font-medium text-fg">Identity</h3>
          <div>
            <label class="block text-muted mb-1">Your name</label>
            <input data-field="user_name" class="w-full h-10 px-3 rounded-md border border-border bg-bg text-fg" placeholder="(leave blank to skip)" />
          </div>
          <div>
            <label class="block text-muted mb-1">How should the assistant address you?</label>
            <select data-field="user_address_as" class="w-full h-10 px-3 rounded-md border border-border bg-bg text-fg">
              <option value="none">Don't address me by name</option>
              <option value="first_name">By my first name</option>
              <option value="full_name">By my full name</option>
              <option value="title">By a title (Sir / Ma'am / etc)</option>
            </select>
          </div>
          <div data-title-row class="hidden">
            <label class="block text-muted mb-1">Title</label>
            <input data-field="user_title" class="w-full h-10 px-3 rounded-md border border-border bg-bg text-fg" placeholder="Sir" />
          </div>
        </div>
        <div data-error class="hidden text-warn text-xs"></div>
      </form>
      <footer class="p-5 border-t border-border flex justify-end gap-2">
        <button data-cancel type="button" class="h-10 px-4 rounded-md border border-border text-fg hover:bg-bg/40">Cancel</button>
        <button data-save   type="button" class="h-10 px-4 rounded-md bg-accent text-bg font-semibold hover:opacity-90">Save</button>
      </footer>
    `,e.appendChild(this.el),this.el.querySelector("[data-close]").addEventListener("click",()=>this.close()),this.el.querySelector("[data-cancel]").addEventListener("click",()=>this.close()),this.el.querySelector('[data-field="provider"]').addEventListener("change",()=>{this.refreshSecretFields(),this.refreshModelOptions()}),this.el.querySelector('[data-field="user_address_as"]').addEventListener("change",()=>{this.refreshTitleRow()}),this.el.querySelector("[data-toggle-secret]").addEventListener("click",()=>{const t=this.el.querySelector('[data-field="secret"]'),i=this.el.querySelector("[data-eye-show]"),s=this.el.querySelector("[data-eye-hide]"),r=t.type==="text";t.type=r?"password":"text",i.classList.toggle("hidden",!r),s.classList.toggle("hidden",r)}),this.el.querySelector("[data-save]").addEventListener("click",async()=>{const t=this.read(),i=this.el.querySelector("[data-error]"),s=await this.saveHandler(t);s.ok?(i.classList.add("hidden"),this.close()):(i.textContent=(s.errors||["Save failed"]).join(" · "),i.classList.remove("hidden"))})}open(e){this.populate(e),this.el.classList.remove("translate-x-full")}close(){this.el.classList.add("translate-x-full")}onSave(e){this.saveHandler=e}populate(e){this.currentCfg=e,this.el.querySelector('[data-field="provider"]').value=e.provider,this.el.querySelector('[data-field="hotkey"]').value=e.hotkey,this.el.querySelector('[data-field="roots"]').value=e.allowed_roots.join(", "),this.el.querySelector('[data-field="user_name"]').value=e.user_name||"",this.el.querySelector('[data-field="user_address_as"]').value=e.user_address_as||"none",this.el.querySelector('[data-field="user_title"]').value=e.user_title||"",this.refreshModelOptions(),this.refreshSecretFields(),this.refreshTitleRow()}refreshTitleRow(){const e=this.el.querySelector('[data-field="user_address_as"]').value;this.el.querySelector("[data-title-row]").classList.toggle("hidden",e!=="title")}refreshModelOptions(){const e=this.el.querySelector('[data-field="provider"]').value,t=this.el.querySelector('[data-field="model"]'),i=this.currentCfg?.available_models?.[e]??[],s=this.currentCfg?.model;t.innerHTML="";const r=new Set;for(const l of i)r.add(l),t.appendChild(this.makeOption(l));s&&!r.has(s)&&t.appendChild(this.makeOption(s+" (custom)",s)),s&&r.has(s)&&(t.value=s)}makeOption(e,t){const i=document.createElement("option");return i.textContent=e,i.value=t??e,i}refreshSecretFields(){const e=this.el.querySelector('[data-field="provider"]').value,t=this.el.querySelector("[data-secret-label]"),i=this.el.querySelector('[data-field="secret"]'),s=this.el.querySelector("[data-secret-hint]"),r=this.el.querySelector("[data-saved-badge]"),l=this.el.querySelector("[data-eye-show]"),o=this.el.querySelector("[data-eye-hide]");t.textContent=e==="ollama"?"Ollama base URL":"API key",i.value="",i.type=e==="ollama"?"text":"password",l.classList.remove("hidden"),o.classList.add("hidden");const n=e===this.currentCfg?.provider&&this.currentCfg?.has_secret===!0;r.classList.toggle("hidden",!n),e==="ollama"?(i.placeholder=this.currentCfg?.ollama_base_url||"http://localhost:11434",s.textContent="URL of your local Ollama instance."):n?(i.placeholder="✓ key on file — leave blank to keep current",s.textContent="Stored in ~/.voice-assistant/.env, mode 0600. Type a new key only to replace it."):(i.placeholder=e==="anthropic"?"sk-ant-…":e==="openai"?"sk-…":"AIza…",s.textContent="Stored in ~/.voice-assistant/.env, mode 0600.")}read(){const e=this.el.querySelector('[data-field="provider"]').value,t=this.el.querySelector('[data-field="model"]').value.trim(),i=this.el.querySelector('[data-field="hotkey"]').value.trim(),s=this.el.querySelector('[data-field="roots"]').value.split(",").map(m=>m.trim()).filter(Boolean),r=this.el.querySelector('[data-field="secret"]').value.trim(),l=this.el.querySelector('[data-field="user_name"]').value.trim()||null,o=this.el.querySelector('[data-field="user_address_as"]').value,n=this.el.querySelector('[data-field="user_title"]').value.trim()||null,h={provider:e,model:t,hotkey:i,allowed_roots:s,ollama_base_url:e==="ollama"?r||this.currentCfg?.ollama_base_url||"http://localhost:11434":null,user_name:l,user_address_as:o,user_title:n};return e!=="ollama"&&r&&(h._secret=r),h}}class q{el;timer=null;constructor(e){this.el=document.createElement("div"),this.el.className="fixed top-16 left-1/2 -translate-x-1/2 px-4 py-2 rounded-md text-sm font-medium opacity-0 pointer-events-none transition-opacity duration-200 z-40",e.appendChild(this.el)}show(e,t){this.timer!==null&&clearTimeout(this.timer);const i={info:"bg-surface border border-border text-fg",warn:"bg-warn/10 border border-warn/40 text-warn",error:"bg-warn/10 border border-warn/40 text-warn"};this.el.className=`fixed top-16 left-1/2 -translate-x-1/2 px-4 py-2 rounded-md text-sm font-medium opacity-100 transition-opacity duration-200 z-40 ${i[e]}`,this.el.textContent=t,this.timer=window.setTimeout(()=>{this.el.classList.replace("opacity-100","opacity-0")},4e3)}}class E{listeners=[];emit(e){for(const t of this.listeners)t(e)}on(e){return this.listeners.push(e),()=>{this.listeners=this.listeners.filter(t=>t!==e)}}}const g=new E;window.va={emit:a=>g.emit(a)};const d=()=>typeof window<"u"&&typeof window.pywebview<"u",u={startListening:async()=>d()?window.pywebview.api.start_listening():void 0,stopListening:async()=>d()?window.pywebview.api.stop_listening():void 0,sendText:async a=>d()?window.pywebview.api.send_text(a):void 0,getConfig:async()=>d()?window.pywebview.api.get_config():{provider:"anthropic",model:"claude-sonnet-4-6",hotkey:"ctrl+shift+space",allowed_roots:["~"],ollama_base_url:null},saveConfig:async a=>d()?window.pywebview.api.save_config(a):{ok:!0},quit:async()=>d()?window.pywebview.api.quit():void 0};d()?document.addEventListener("pywebviewready",()=>{u.getConfig().then(a=>g.emit({type:"config",cfg:a}))}):setTimeout(async()=>{const a=await u.getConfig();g.emit({type:"config",cfg:a})},100);const c=document.getElementById("app");c.className="h-screen flex flex-col";c.innerHTML="";const b=new S(c),x=new k(c),f=new C(c),y=new _(c),v=new L(document.body),M=new q(document.body),w=c.children[2];w.classList.remove("flex-1");w.classList.add("max-h-48","shrink-0");let p=null;g.on(a=>{switch(a.type){case"status":b.setStatus(a.value),x.setState(a.value);break;case"transcript":f.push({speaker:a.speaker,text:a.text,tool_call:a.tool_call});break;case"transcript_start":a.speaker==="assistant"&&f.startAssistant();break;case"transcript_chunk":f.appendAssistant(a.text),b&&b.setStatus("speaking"),x.setState("speaking");break;case"transcript_end":f.endAssistant();break;case"audio_level":x.setRms(a.rms);break;case"config":p=a.cfg;break;case"toast":M.show(a.level,a.message);break}});y.onSubmit(a=>{u.sendText(a)});y.onRecord(()=>{u.startListening()});b.onSettingsClick(()=>{p&&v.open(p)});v.onSave(async a=>u.saveConfig(a));document.addEventListener("keydown",a=>{a.key==="Escape"&&v.close(),(a.metaKey||a.ctrlKey)&&a.key===","&&(a.preventDefault(),p&&v.open(p))});
