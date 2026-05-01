(function(){const e=document.createElement("link").relList;if(e&&e.supports&&e.supports("modulepreload"))return;for(const a of document.querySelectorAll('link[rel="modulepreload"]'))i(a);new MutationObserver(a=>{for(const r of a)if(r.type==="childList")for(const o of r.addedNodes)o.tagName==="LINK"&&o.rel==="modulepreload"&&i(o)}).observe(document,{childList:!0,subtree:!0});function t(a){const r={};return a.integrity&&(r.integrity=a.integrity),a.referrerPolicy&&(r.referrerPolicy=a.referrerPolicy),a.crossOrigin==="use-credentials"?r.credentials="include":a.crossOrigin==="anonymous"?r.credentials="omit":r.credentials="same-origin",r}function i(a){if(a.ep)return;a.ep=!0;const r=t(a);fetch(a.href,r)}})();class T{el;constructor(e){this.el=document.createElement("header"),this.el.className="h-12 px-5 flex items-center justify-between border-b border-border bg-surface/40",this.el.innerHTML=`
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
    `,e.appendChild(this.el)}setStatus(e){const t=this.el.querySelector("[data-status]");t&&(t.textContent=e)}onSettingsClick(e){this.el.querySelector("[data-settings]").addEventListener("click",e)}}const y={aria:"/avatars/aria.svg",liam:"/avatars/liam.svg",sage:"/avatars/sage.svg"};class A{el;img;halo;dots;constructor(e,t="aria"){this.el=document.createElement("div"),this.el.className="flex-1 grid place-items-center relative",this.el.innerHTML=`
      <div data-halo class="absolute h-72 w-72 rounded-full opacity-0 transition-opacity duration-300"
        style="background: radial-gradient(closest-side, rgba(149,128,255,0.45), transparent 70%); filter: blur(40px);"></div>
      <img data-img alt="assistant avatar" class="relative h-56 w-56 rounded-full object-cover shadow-2xl shadow-black/40 border-2 border-border"
        style="background: linear-gradient(135deg, #1f242c, #0b0d10);" />
      <div data-dots class="absolute -top-4 hidden gap-1.5">
        <span class="block h-2 w-2 rounded-full bg-accent animate-bounce"></span>
        <span class="block h-2 w-2 rounded-full bg-accent animate-bounce" style="animation-delay: 0.15s"></span>
        <span class="block h-2 w-2 rounded-full bg-accent animate-bounce" style="animation-delay: 0.30s"></span>
      </div>
      <p data-hint class="absolute bottom-12 text-sm text-muted">Press the hotkey to talk</p>
    `,e.appendChild(this.el),this.img=this.el.querySelector("[data-img]"),this.halo=this.el.querySelector("[data-halo]"),this.dots=this.el.querySelector("[data-dots]"),this.setAvatar(t),this.startBreathing()}setAvatar(e){const t=y[e]??y.aria;this.img.src=t}setState(e){const t=this.el.querySelector("[data-hint]");t.textContent={idle:"Press the hotkey to talk",listening:"Listening…",thinking:"Thinking…",speaking:"",error:"Something went wrong."}[e],(a=>{this.halo.style.opacity=a})(e==="listening"||e==="speaking"?"1":e==="thinking"?"0.4":e==="error"?"0":"0.6"),this.dots.classList.toggle("hidden",e!=="thinking"),this.dots.classList.toggle("flex",e==="thinking"),e==="speaking"?this.img.style.animation="va-bob 0.4s ease-in-out infinite alternate":e==="listening"?this.img.style.animation="va-bob 1.2s ease-in-out infinite alternate":this.img.style.animation="va-breathe 4s ease-in-out infinite"}setRms(e){}startBreathing(){if(!document.querySelector("#va-avatar-keyframes")){const e=document.createElement("style");e.id="va-avatar-keyframes",e.textContent=`
        @keyframes va-breathe { 0%,100% { transform: scale(1); } 50% { transform: scale(1.02); } }
        @keyframes va-bob { 0% { transform: translateY(0); } 100% { transform: translateY(-4px); } }
        @media (prefers-reduced-motion: reduce) {
          [data-img] { animation: none !important; }
        }
      `,document.head.appendChild(e)}this.img.style.animation="va-breathe 4s ease-in-out infinite"}destroy(){}}class M{el;streamingLine=null;constructor(e){this.el=document.createElement("section"),this.el.className="flex-1 overflow-y-auto px-5 py-4 space-y-3",this.el.innerHTML='<p class="text-dim text-sm">Press the hotkey or type a command to start.</p>',e.appendChild(this.el)}push(e){this.el.querySelector("p.text-dim")&&this.el.replaceChildren();const t=document.createElement("div");t.className="flex gap-3";const i=e.speaker==="user"?'<span class="text-xs text-dim shrink-0 mt-0.5 w-16">you</span>':'<span class="text-xs text-accent shrink-0 mt-0.5 w-16">assistant</span>',a=document.createElement("p");if(a.className="text-sm leading-6 text-fg",a.textContent=e.text,t.innerHTML=i,t.appendChild(a),e.tool_call){const r=document.createElement("pre");r.className="text-xs text-muted font-mono ml-19 mt-1",r.textContent=`↳ ${e.tool_call}`,t.appendChild(r)}this.el.appendChild(t),this.el.scrollTop=this.el.scrollHeight}startAssistant(){this.el.querySelector("p.text-dim")&&this.el.replaceChildren();const e=document.createElement("div");e.className="flex gap-3",e.innerHTML='<span class="text-xs text-accent shrink-0 mt-0.5 w-16">assistant</span>';const t=document.createElement("p");t.className="text-sm leading-6 text-fg",t.textContent="",e.appendChild(t),this.el.appendChild(e),this.streamingLine=t,this.el.scrollTop=this.el.scrollHeight}appendAssistant(e){this.streamingLine||this.startAssistant(),this.streamingLine.textContent=(this.streamingLine.textContent||"")+e,this.el.scrollTop=this.el.scrollHeight}endAssistant(){this.streamingLine=null}replayHistory(e){if(e.length!==0){this.el.querySelector("p.text-dim")&&this.el.replaceChildren();for(const t of e)this.push({speaker:t.speaker,text:t.text})}}}class N{el;input;submitHandler=()=>{};recordHandler=()=>{};constructor(e){this.el=document.createElement("footer"),this.el.className="p-4 border-t border-border bg-surface/40 flex gap-2",this.el.innerHTML=`
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
    `,e.appendChild(this.el),this.input=this.el.querySelector("[data-input]"),this.input.addEventListener("keydown",t=>{t.key==="Enter"&&this.input.value.trim()&&(this.submitHandler(this.input.value.trim()),this.input.value="")}),this.el.querySelector("[data-record]").addEventListener("click",()=>this.recordHandler())}onSubmit(e){this.submitHandler=e}onRecord(e){this.recordHandler=e}}class O{el;saveHandler=async()=>({ok:!0});currentCfg=null;constructor(e){this.el=document.createElement("aside"),this.el.className="fixed inset-y-0 right-0 w-full max-w-md bg-surface border-l border-border translate-x-full transition-transform duration-200 ease-out z-30 flex flex-col",this.el.innerHTML=`
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
    `,e.appendChild(this.el),this.el.querySelector("[data-close]").addEventListener("click",()=>this.close()),this.el.querySelector("[data-cancel]").addEventListener("click",()=>this.close()),this.el.querySelector('[data-field="provider"]').addEventListener("change",()=>{this.refreshSecretFields(),this.refreshModelOptions()}),this.el.querySelector('[data-field="user_address_as"]').addEventListener("change",()=>{this.refreshTitleRow()}),this.el.querySelector("[data-toggle-secret]").addEventListener("click",()=>{const t=this.el.querySelector('[data-field="secret"]'),i=this.el.querySelector("[data-eye-show]"),a=this.el.querySelector("[data-eye-hide]"),r=t.type==="text";t.type=r?"password":"text",i.classList.toggle("hidden",!r),a.classList.toggle("hidden",r)}),this.el.querySelector("[data-save]").addEventListener("click",async()=>{const t=this.read(),i=this.el.querySelector("[data-error]"),a=await this.saveHandler(t);a.ok?(i.classList.add("hidden"),this.close()):(i.textContent=(a.errors||["Save failed"]).join(" · "),i.classList.remove("hidden"))})}open(e){this.populate(e),this.el.classList.remove("translate-x-full")}close(){this.el.classList.add("translate-x-full")}onSave(e){this.saveHandler=e}populate(e){this.currentCfg=e,this.el.querySelector('[data-field="provider"]').value=e.provider,this.el.querySelector('[data-field="hotkey"]').value=e.hotkey,this.el.querySelector('[data-field="roots"]').value=e.allowed_roots.join(", "),this.el.querySelector('[data-field="user_name"]').value=e.user_name||"",this.el.querySelector('[data-field="user_address_as"]').value=e.user_address_as||"none",this.el.querySelector('[data-field="user_title"]').value=e.user_title||"",this.refreshModelOptions(),this.refreshSecretFields(),this.refreshTitleRow()}refreshTitleRow(){const e=this.el.querySelector('[data-field="user_address_as"]').value;this.el.querySelector("[data-title-row]").classList.toggle("hidden",e!=="title")}refreshModelOptions(){const e=this.el.querySelector('[data-field="provider"]').value,t=this.el.querySelector('[data-field="model"]'),i=this.currentCfg?.available_models?.[e]??[],a=this.currentCfg?.model;t.innerHTML="";const r=new Set;for(const o of i)r.add(o),t.appendChild(this.makeOption(o));a&&!r.has(a)&&t.appendChild(this.makeOption(a+" (custom)",a)),a&&r.has(a)&&(t.value=a)}makeOption(e,t){const i=document.createElement("option");return i.textContent=e,i.value=t??e,i}refreshSecretFields(){const e=this.el.querySelector('[data-field="provider"]').value,t=this.el.querySelector("[data-secret-label]"),i=this.el.querySelector('[data-field="secret"]'),a=this.el.querySelector("[data-secret-hint]"),r=this.el.querySelector("[data-saved-badge]"),o=this.el.querySelector("[data-eye-show]"),g=this.el.querySelector("[data-eye-hide]");t.textContent=e==="ollama"?"Ollama base URL":"API key",i.value="",i.type=e==="ollama"?"text":"password",o.classList.remove("hidden"),g.classList.add("hidden");const p=e===this.currentCfg?.provider&&this.currentCfg?.has_secret===!0;r.classList.toggle("hidden",!p),e==="ollama"?(i.placeholder=this.currentCfg?.ollama_base_url||"http://localhost:11434",a.textContent="URL of your local Ollama instance."):p?(i.placeholder="✓ key on file — leave blank to keep current",a.textContent="Stored in ~/.voice-assistant/.env, mode 0600. Type a new key only to replace it."):(i.placeholder=e==="anthropic"?"sk-ant-…":e==="openai"?"sk-…":"AIza…",a.textContent="Stored in ~/.voice-assistant/.env, mode 0600.")}read(){const e=this.el.querySelector('[data-field="provider"]').value,t=this.el.querySelector('[data-field="model"]').value.trim(),i=this.el.querySelector('[data-field="hotkey"]').value.trim(),a=this.el.querySelector('[data-field="roots"]').value.split(",").map(H=>H.trim()).filter(Boolean),r=this.el.querySelector('[data-field="secret"]').value.trim(),o=this.el.querySelector('[data-field="user_name"]').value.trim()||null,g=this.el.querySelector('[data-field="user_address_as"]').value,p=this.el.querySelector('[data-field="user_title"]').value.trim()||null,S=this.el.querySelector('[data-field="voice"]'),C=this.el.querySelector('[data-field="stt_language"]'),_=this.el.querySelector('[data-field="avatar"] [aria-pressed="true"]'),q=S?.value||this.currentCfg?.voice||"piper:en_US-amy-medium",L=C?.value||this.currentCfg?.stt_language||"auto",E=_?.dataset.avatar??this.currentCfg?.avatar??"aria",v={provider:e,model:t,hotkey:i,allowed_roots:a,ollama_base_url:e==="ollama"?r||this.currentCfg?.ollama_base_url||"http://localhost:11434":null,user_name:o,user_address_as:g,user_title:p,voice:q,stt_language:L,avatar:E};return e!=="ollama"&&r&&(v._secret=r),v}}class R{el;timer=null;constructor(e){this.el=document.createElement("div"),this.el.className="fixed top-16 left-1/2 -translate-x-1/2 px-4 py-2 rounded-md text-sm font-medium opacity-0 pointer-events-none transition-opacity duration-200 z-40",e.appendChild(this.el)}show(e,t){this.timer!==null&&clearTimeout(this.timer);const i={info:"bg-surface border border-border text-fg",warn:"bg-warn/10 border border-warn/40 text-warn",error:"bg-warn/10 border border-warn/40 text-warn"};this.el.className=`fixed top-16 left-1/2 -translate-x-1/2 px-4 py-2 rounded-md text-sm font-medium opacity-100 transition-opacity duration-200 z-40 ${i[e]}`,this.el.textContent=t,this.timer=window.setTimeout(()=>{this.el.classList.replace("opacity-100","opacity-0")},4e3)}}class B{listeners=[];emit(e){for(const t of this.listeners)t(e)}on(e){return this.listeners.push(e),()=>{this.listeners=this.listeners.filter(t=>t!==e)}}}const h=new B;window.va={emit:s=>h.emit(s)};const l=()=>typeof window<"u"&&typeof window.pywebview<"u",d={startListening:async()=>l()?window.pywebview.api.start_listening():void 0,stopListening:async()=>l()?window.pywebview.api.stop_listening():void 0,sendText:async s=>l()?window.pywebview.api.send_text(s):void 0,getConfig:async()=>l()?window.pywebview.api.get_config():{provider:"anthropic",model:"claude-sonnet-4-6",hotkey:"ctrl+shift+space",allowed_roots:["~"],ollama_base_url:null},saveConfig:async s=>l()?window.pywebview.api.save_config(s):{ok:!0},getHistory:async()=>l()?window.pywebview.api.get_history():[],quit:async()=>l()?window.pywebview.api.quit():void 0};l()?document.addEventListener("pywebviewready",()=>{d.getConfig().then(s=>h.emit({type:"config",cfg:s})),d.getHistory().then(s=>h.emit({type:"history_replay",items:s}))}):setTimeout(async()=>{const s=await d.getConfig();h.emit({type:"config",cfg:s})},100);const n=document.getElementById("app");n.className="h-screen flex flex-col";n.innerHTML="";const f=new T(n),m=new A(n,"aria"),u=new M(n),w=new N(n),b=new O(document.body),P=new R(document.body),k=n.children[2];k.classList.remove("flex-1");k.classList.add("max-h-48","shrink-0");let c=null;h.on(s=>{switch(s.type){case"status":f.setStatus(s.value),m.setState(s.value);break;case"transcript":u.push({speaker:s.speaker,text:s.text,tool_call:s.tool_call});break;case"transcript_start":s.speaker==="assistant"&&u.startAssistant();break;case"transcript_chunk":u.appendAssistant(s.text),f&&f.setStatus("speaking"),m.setState("speaking");break;case"transcript_end":u.endAssistant();break;case"audio_level":m.setRms(s.rms);break;case"config":c=s.cfg,m.setAvatar(c.avatar??"aria");break;case"toast":P.show(s.level,s.message);break;case"history_replay":u.replayHistory(s.items);break}});w.onSubmit(s=>{d.sendText(s)});w.onRecord(()=>{d.startListening()});f.onSettingsClick(()=>{c&&b.open(c)});b.onSave(async s=>d.saveConfig(s));function x(){return document.querySelector("footer [data-input]")}document.addEventListener("keydown",s=>{const e=s.target,t=e&&(e.tagName==="INPUT"||e.tagName==="TEXTAREA"||e.tagName==="SELECT");if((s.metaKey||s.ctrlKey)&&s.key===","){s.preventDefault(),c&&b.open(c);return}if(s.key==="Escape"){b.close();return}if(!t){if(s.key==="/"){s.preventDefault(),x()?.focus();return}if((s.metaKey||s.ctrlKey)&&s.key==="k"){s.preventDefault(),x()?.focus();return}}});
