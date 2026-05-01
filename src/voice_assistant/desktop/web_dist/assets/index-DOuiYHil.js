(function(){const e=document.createElement("link").relList;if(e&&e.supports&&e.supports("modulepreload"))return;for(const s of document.querySelectorAll('link[rel="modulepreload"]'))a(s);new MutationObserver(s=>{for(const r of s)if(r.type==="childList")for(const n of r.addedNodes)n.tagName==="LINK"&&n.rel==="modulepreload"&&a(n)}).observe(document,{childList:!0,subtree:!0});function t(s){const r={};return s.integrity&&(r.integrity=s.integrity),s.referrerPolicy&&(r.referrerPolicy=s.referrerPolicy),s.crossOrigin==="use-credentials"?r.credentials="include":s.crossOrigin==="anonymous"?r.credentials="omit":r.credentials="same-origin",r}function a(s){if(s.ep)return;s.ep=!0;const r=t(s);fetch(s.href,r)}})();class U{el;constructor(e){if(this.el=document.createElement("div"),this.el.className="va-bg",this.el.setAttribute("aria-hidden","true"),this.el.innerHTML=`
      <div class="va-bg__blob va-bg__blob--a"></div>
      <div class="va-bg__blob va-bg__blob--b"></div>
    `,e.insertBefore(this.el,e.firstChild),!document.querySelector("#va-bg-style")){const t=document.createElement("style");t.id="va-bg-style",t.textContent=`
        .va-bg {
          position: fixed;
          inset: 0;
          z-index: 0;
          pointer-events: none;
          background: linear-gradient(135deg, #0b0d10 0%, #15101f 50%, #0b0d10 100%);
          overflow: hidden;
        }
        .va-bg__blob {
          position: absolute;
          border-radius: 50%;
          filter: blur(80px);
          opacity: 0.18;
        }
        .va-bg__blob--a {
          width: 600px;
          height: 600px;
          background: radial-gradient(closest-side, #9580ff, transparent);
          top: -200px;
          left: -150px;
          animation: va-blob-a 18s ease-in-out infinite alternate;
        }
        .va-bg__blob--b {
          width: 500px;
          height: 500px;
          background: radial-gradient(closest-side, #6050cc, transparent);
          bottom: -180px;
          right: -100px;
          animation: va-blob-b 22s ease-in-out infinite alternate;
        }
        @keyframes va-blob-a {
          0%   { transform: translate(0, 0) scale(1); }
          50%  { transform: translate(80px, 60px) scale(1.08); }
          100% { transform: translate(160px, 120px) scale(0.94); }
        }
        @keyframes va-blob-b {
          0%   { transform: translate(0, 0) scale(1); }
          50%  { transform: translate(-60px, -40px) scale(1.1); }
          100% { transform: translate(-120px, -80px) scale(0.92); }
        }
        @media (prefers-reduced-motion: reduce) {
          .va-bg__blob { animation: none !important; }
        }
      `,document.head.appendChild(t)}}destroy(){this.el.remove()}}class W{el;constructor(e){this.el=document.createElement("header"),this.el.className="h-12 px-5 flex items-center justify-between border-b border-border bg-surface/40",this.el.innerHTML=`
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
    `,e.appendChild(this.el)}setStatus(e){const t=this.el.querySelector("[data-status]");t&&(t.textContent=e)}onSettingsClick(e){this.el.querySelector("[data-settings]").addEventListener("click",e)}}const A={aria:"avatars/aria.svg",liam:"avatars/liam.svg",sage:"avatars/sage.svg"};class G{el;img;halo;dots;constructor(e,t="aria"){this.el=document.createElement("div"),this.el.className="flex-1 grid place-items-center relative",this.el.innerHTML=`
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
    `,e.appendChild(this.el),this.img=this.el.querySelector("[data-img]"),this.halo=this.el.querySelector("[data-halo]"),this.dots=this.el.querySelector("[data-dots]"),this.setAvatar(t),this.startBreathing()}setAvatar(e){const t=A[e]??A.aria;this.img.src=t}setState(e){const t=this.el.querySelector("[data-hint]");t.textContent={idle:"Press the hotkey to talk",listening:"Listening…",thinking:"Thinking…",speaking:"",error:"Something went wrong."}[e],(s=>{this.halo.style.opacity=s})(e==="listening"||e==="speaking"?"1":e==="thinking"?"0.4":e==="error"?"0":"0.6"),this.dots.classList.toggle("hidden",e!=="thinking"),this.dots.classList.toggle("flex",e==="thinking"),e==="speaking"?this.img.style.animation="va-bob 0.4s ease-in-out infinite alternate":e==="listening"?this.img.style.animation="va-bob 1.2s ease-in-out infinite alternate":this.img.style.animation="va-breathe 4s ease-in-out infinite"}setRms(e){}startBreathing(){if(!document.querySelector("#va-avatar-keyframes")){const e=document.createElement("style");e.id="va-avatar-keyframes",e.textContent=`
        @keyframes va-breathe { 0%,100% { transform: scale(1); } 50% { transform: scale(1.02); } }
        @keyframes va-bob { 0% { transform: translateY(0); } 100% { transform: translateY(-4px); } }
        @media (prefers-reduced-motion: reduce) {
          [data-img] { animation: none !important; }
        }
      `,document.head.appendChild(e)}this.img.style.animation="va-breathe 4s ease-in-out infinite"}destroy(){}}const X={"tab.brain":"Brain","tab.voice":"Voice","tab.audio":"Audio","tab.identity":"Identity","tab.privacy":"Privacy & Display","settings.title":"Settings","settings.close":"Close settings","settings.save":"Save","settings.cancel":"Cancel","composer.placeholder":"Type a command…","composer.start_listening":"Start listening","composer.recording":"Recording…","composer.send":"Send message","transcript.prompt":"Press the hotkey or type a command to start.","history.title":"History","history.empty":"No history yet.","toast.save_failed":"Save failed","provider.label":"Provider","model.label":"Model","api_key.label":"API key","api_key.saved":"✓ saved","reply_language.label":"Reply language","reply_language.hint":"Override auto-detection and always reply in this language.","avatar.label":"Avatar","voice.label":"Voice","voice.test":"▶ Test this voice","stt_language.label":"Speech recognition language","trigger.label":"Trigger","hotkey.label":"Hotkey","wake_word.label":"Wake word","sensitivity.label":"Sensitivity","sensitivity.hint":"Higher = fewer false positives but easier to miss.","user_name.label":"Your name","user_name.placeholder":"(leave blank to skip)","address_as.label":"How should the assistant address you?","title.label":"Title","allowed_folders.label":"Allowed folders (comma-separated)","allowed_folders.hint":"The assistant may only read/write files in these directories.","display.group":"Display","display.high_contrast":"High contrast","display.font_size":"Font size","display.font_small":"Small","display.font_medium":"Medium","display.font_large":"Large","display.font_xl":"Extra large","ai_act.footer":"AI assistant powered by {provider}. Inputs are sent to {provider}.","transparency.title":"AI System Disclosure","transparency.body":"voice-assistant is an AI system. It uses external LLM providers (configurable). Your inputs (text/voice) are sent to the chosen provider. Tool actions (file ops, email, web, WhatsApp) execute locally with your authorisation.","transparency.ok":"I understand"},J={"tab.brain":"Brain","tab.voice":"Voice","tab.audio":"Audio","tab.identity":"Identity","tab.privacy":"Privacy & Display","settings.title":"Settings","settings.close":"Close settings","settings.save":"Save","settings.cancel":"Cancel","composer.placeholder":"Type a command…","composer.start_listening":"Start listening","composer.recording":"Recording…","composer.send":"Send message","transcript.prompt":"Press the hotkey or type a command to start.","history.title":"History","history.empty":"No history yet.","toast.save_failed":"Save failed","provider.label":"Provider","model.label":"Model","api_key.label":"API key","api_key.saved":"✓ saved","reply_language.label":"Reply language","reply_language.hint":"Override auto-detection and always reply in this language.","avatar.label":"Avatar","voice.label":"Voice","voice.test":"▶ Test this voice","stt_language.label":"Speech recognition language","trigger.label":"Trigger","hotkey.label":"Hotkey","wake_word.label":"Wake word","sensitivity.label":"Sensitivity","sensitivity.hint":"Higher = fewer false positives but easier to miss.","user_name.label":"Your name","user_name.placeholder":"(leave blank to skip)","address_as.label":"How should the assistant address you?","title.label":"Title","allowed_folders.label":"Allowed folders (comma-separated)","allowed_folders.hint":"The assistant may only read/write files in these directories.","display.group":"Display","display.high_contrast":"High contrast","display.font_size":"Font size","display.font_small":"Small","display.font_medium":"Medium","display.font_large":"Large","display.font_xl":"Extra large","ai_act.footer":"AI assistant powered by {provider}. Inputs are sent to {provider}.","transparency.title":"AI System Disclosure","transparency.body":"voice-assistant is an AI system. It uses external LLM providers (configurable). Your inputs (text/voice) are sent to the chosen provider. Tool actions (file ops, email, web, WhatsApp) execute locally with your authorisation.","transparency.ok":"I understand"},Q={"tab.brain":"Brain","tab.voice":"Voice","tab.audio":"Audio","tab.identity":"Identity","tab.privacy":"Privacy & Display","settings.title":"Settings","settings.close":"Close settings","settings.save":"Save","settings.cancel":"Cancel","composer.placeholder":"Type a command…","composer.start_listening":"Start listening","composer.recording":"Recording…","composer.send":"Send message","transcript.prompt":"Press the hotkey or type a command to start.","history.title":"History","history.empty":"No history yet.","toast.save_failed":"Save failed","provider.label":"Provider","model.label":"Model","api_key.label":"API key","api_key.saved":"✓ saved","reply_language.label":"Reply language","reply_language.hint":"Override auto-detection and always reply in this language.","avatar.label":"Avatar","voice.label":"Voice","voice.test":"▶ Test this voice","stt_language.label":"Speech recognition language","trigger.label":"Trigger","hotkey.label":"Hotkey","wake_word.label":"Wake word","sensitivity.label":"Sensitivity","sensitivity.hint":"Higher = fewer false positives but easier to miss.","user_name.label":"Your name","user_name.placeholder":"(leave blank to skip)","address_as.label":"How should the assistant address you?","title.label":"Title","allowed_folders.label":"Allowed folders (comma-separated)","allowed_folders.hint":"The assistant may only read/write files in these directories.","display.group":"Display","display.high_contrast":"High contrast","display.font_size":"Font size","display.font_small":"Small","display.font_medium":"Medium","display.font_large":"Large","display.font_xl":"Extra large","ai_act.footer":"AI assistant powered by {provider}. Inputs are sent to {provider}.","transparency.title":"AI System Disclosure","transparency.body":"voice-assistant is an AI system. It uses external LLM providers (configurable). Your inputs (text/voice) are sent to the chosen provider. Tool actions (file ops, email, web, WhatsApp) execute locally with your authorisation.","transparency.ok":"I understand"},S=X,Z=J,ee=Q,E={en:S,ur:Z,hi:ee};let B=S,H="en";function o(i){return B[i]??S[i]??i}function te(i){const e=i.split("-")[0];B=E[e]??E[i]??S,H=e,document.dispatchEvent(new CustomEvent("va:locale-change",{detail:{code:H}}))}class ae{el;streamingBubble=null;streamingBody=null;turnCounter=0;constructor(e){this.el=document.createElement("section"),this.el.className="va-transcript flex-1 overflow-y-auto px-4 py-4 flex flex-col gap-3",this.el.innerHTML=`<p class="text-dim text-sm text-center mt-8 select-none">${o("transcript.prompt")}</p>`,e.appendChild(this.el),this._injectStyles()}push(e){this._clearPlaceholder();const t=`turn-${++this.turnCounter}`,a=this._makeBubble(e.speaker,e.text,t);if(e.tool_call){const s=document.createElement("p");s.className="va-tool-call text-xs text-dim italic mt-1 px-1",s.textContent=`↳ ${e.tool_call}`,a.appendChild(s)}this.el.appendChild(a),this._scrollToBottom()}startAssistant(){this.streamingBubble=null,this.streamingBody=null}appendAssistant(e){if(!this.streamingBody){this._clearPlaceholder();const t=`turn-${++this.turnCounter}`,a=document.createElement("div");a.className="va-bubble-row va-bubble-row--assistant va-reveal",a.dataset.turnId=t,a.innerHTML=`
        <div class="va-bubble va-bubble--assistant">
          <span class="va-bubble-body"></span><span class="va-cursor" aria-hidden="true">▋</span>
        </div>
      `,this.el.appendChild(a),this.streamingBubble=a,this.streamingBody=a.querySelector(".va-bubble-body"),requestAnimationFrame(()=>a.classList.add("is-visible"))}this.streamingBody.textContent=(this.streamingBody.textContent||"")+e,this._scrollToBottom()}endAssistant(){this.streamingBubble&&this.streamingBubble.querySelector(".va-cursor")?.remove(),this.streamingBubble=null,this.streamingBody=null}replayHistory(e){if(e.length!==0){this._clearPlaceholder();for(const t of e)this.push({speaker:t.speaker,text:t.text})}}_clearPlaceholder(){const e=this.el.querySelector("p.text-dim");e&&e.remove()}_makeBubble(e,t,a){const s=document.createElement("div");s.className=`va-bubble-row va-bubble-row--${e} va-reveal`,s.dataset.turnId=a;const r=document.createElement("div");r.className=`va-bubble va-bubble--${e}`;const n=document.createElement("span");return n.className="va-bubble-body",n.textContent=t,r.appendChild(n),s.appendChild(r),requestAnimationFrame(()=>s.classList.add("is-visible")),s}_scrollToBottom(){this.el.scrollTop=this.el.scrollHeight}_injectStyles(){if(document.querySelector("#va-transcript-style"))return;const e=document.createElement("style");e.id="va-transcript-style",e.textContent=`
      .va-transcript { scrollbar-width: thin; scrollbar-color: #2a2d38 transparent; }
      .va-transcript::-webkit-scrollbar { width: 4px; }
      .va-transcript::-webkit-scrollbar-thumb { background: #2a2d38; border-radius: 2px; }

      .va-bubble-row {
        display: flex;
        max-width: 100%;
        opacity: 0;
        transform: translateY(8px);
        transition: opacity 200ms cubic-bezier(0.2, 0.8, 0.2, 1),
                    transform 200ms cubic-bezier(0.2, 0.8, 0.2, 1);
      }
      .va-bubble-row.is-visible { opacity: 1; transform: translateY(0); }

      /* RTL-aware alignment using logical values */
      .va-bubble-row--user    { justify-content: flex-end; }
      .va-bubble-row--assistant { justify-content: flex-start; }
      /* In RTL: user bubble aligns inline-end (right in LTR, left in RTL) */
      [dir="rtl"] .va-bubble-row--user    { justify-content: flex-start; }
      [dir="rtl"] .va-bubble-row--assistant { justify-content: flex-end; }

      .va-bubble {
        max-width: 70%;
        padding: 10px 14px;
        border-radius: 18px;
        font-size: 0.875rem;
        line-height: 1.5;
        word-break: break-word;
        display: flex;
        flex-direction: column;
        gap: 4px;
      }
      .va-bubble--user {
        background: rgba(149, 128, 255, 0.18);
        border: 1px solid rgba(149, 128, 255, 0.28);
        color: #e8e6ff;
        border-end-end-radius: 4px;   /* bottom-right in LTR, bottom-left in RTL */
      }
      .va-bubble--assistant {
        background: rgba(30, 34, 46, 0.7);
        border: 1px solid rgba(255,255,255,0.07);
        backdrop-filter: blur(8px);
        color: #d8dce8;
        border-end-start-radius: 4px; /* bottom-left in LTR, bottom-right in RTL */
      }
      .va-cursor {
        display: inline-block;
        margin-left: 2px;
        opacity: 0.7;
        animation: va-blink 0.9s step-end infinite;
        font-size: 0.8em;
      }
      @keyframes va-blink {
        0%, 100% { opacity: 0.7; }
        50%       { opacity: 0; }
      }
      .va-tool-call { display: block; }

      @media (prefers-reduced-motion: reduce) {
        .va-bubble-row { transition: none; opacity: 1; transform: none; }
        .va-cursor { animation: none; }
      }
    `,document.head.appendChild(e)}destroy(){}}class ie{el;BAR_COUNT=20;constructor(e){this.el=document.createElement("div"),this.el.className="va-wave hidden",this.el.setAttribute("aria-hidden","true");for(let t=0;t<this.BAR_COUNT;t++){const a=document.createElement("span");a.className="va-wave__bar";const s=(Math.random()*.6).toFixed(2),r=(.5+Math.random()*.5).toFixed(2);a.style.cssText=`animation-delay: ${s}s; animation-duration: ${r}s;`,this.el.appendChild(a)}e.appendChild(this.el),this._injectStyles()}show(){this.el.classList.remove("hidden")}hide(){this.el.classList.add("hidden")}destroy(){this.el.remove()}_injectStyles(){if(document.querySelector("#va-wave-style"))return;const e=document.createElement("style");e.id="va-wave-style",e.textContent=`
      .va-wave {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 3px;
        height: 40px;
        padding: 0 12px;
      }
      .va-wave.hidden { display: none; }

      .va-wave__bar {
        display: inline-block;
        width: 3px;
        min-height: 4px;
        border-radius: 2px;
        background: var(--color-accent, #9580ff);
        animation: va-wave-bar 0.5s ease-in-out infinite alternate;
        transform-origin: bottom;
      }
      @keyframes va-wave-bar {
        0%   { transform: scaleY(0.2); opacity: 0.5; }
        100% { transform: scaleY(1.0); opacity: 1.0; }
      }
      @media (prefers-reduced-motion: reduce) {
        .va-wave__bar { animation: none; transform: scaleY(0.5); }
      }
    `,document.head.appendChild(e)}}class se{el;input;micBtn;sendBtn;submitHandler=()=>{};recordHandler=()=>{};constructor(e){this.el=document.createElement("footer"),this.el.className="va-composer",this.el.innerHTML=`
      <div class="va-composer-inner glass">
        <button data-record type="button" aria-label="${o("composer.start_listening")}" class="va-mic-btn" title="${o("composer.start_listening")}">
          <span data-mic-icon class="va-mic-icon">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
              <rect x="9" y="2" width="6" height="12" rx="3"/>
              <path d="M5 10v2a7 7 0 0 0 14 0v-2"/>
              <line x1="12" y1="19" x2="12" y2="22"/>
            </svg>
          </span>
          <span data-listen-dot class="va-listen-dot hidden" aria-hidden="true"></span>
        </button>
        <textarea data-input rows="1" placeholder="${o("composer.placeholder")}"
          class="va-composer-input" aria-label="${o("composer.placeholder")}"></textarea>
        <button data-send type="button" aria-label="${o("composer.send")}" class="va-send-btn hidden" title="${o("composer.send")}">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
            <line x1="22" y1="2" x2="11" y2="13"/>
            <polygon points="22 2 15 22 11 13 2 9 22 2"/>
          </svg>
        </button>
      </div>
    `,e.appendChild(this.el),this.input=this.el.querySelector("[data-input]"),this.micBtn=this.el.querySelector("[data-record]"),this.sendBtn=this.el.querySelector("[data-send]"),this._wireEvents(),this._injectStyles()}onSubmit(e){this.submitHandler=e}onRecord(e){this.recordHandler=e}setListening(e){const t=this.el.querySelector("[data-mic-icon]"),a=this.el.querySelector("[data-listen-dot]");t.classList.toggle("hidden",e),a.classList.toggle("hidden",!e),this.micBtn.setAttribute("aria-label",o(e?"composer.recording":"composer.start_listening"))}_wireEvents(){this.input.addEventListener("input",()=>{this._resize(),this._toggleSend()}),this.input.addEventListener("keydown",e=>{e.key==="Enter"&&!e.shiftKey&&(e.preventDefault(),this._submit())}),this.sendBtn.addEventListener("click",()=>this._submit()),this.micBtn.addEventListener("click",()=>this.recordHandler())}_submit(){const e=this.input.value.trim();e&&(this.submitHandler(e),this.input.value="",this._resize(),this._toggleSend())}_resize(){this.input.style.height="auto";const t=24*4+16;this.input.style.height=Math.min(this.input.scrollHeight,t)+"px"}_toggleSend(){const e=this.input.value.trim().length>0;this.sendBtn.classList.toggle("hidden",!e)}_injectStyles(){if(document.querySelector("#va-composer-style"))return;const e=document.createElement("style");e.id="va-composer-style",e.textContent=`
      .va-composer {
        padding: 10px 12px 12px;
        flex-shrink: 0;
      }
      .va-composer-inner {
        display: flex;
        align-items: flex-end;
        gap: 8px;
        border-radius: 16px;
        padding: 8px 10px;
      }
      .va-composer-input {
        flex: 1;
        background: transparent;
        border: none;
        outline: none;
        resize: none;
        font: inherit;
        font-size: 0.875rem;
        color: #e0e4f0;
        line-height: 1.5;
        min-height: 24px;
        max-height: 112px;
        overflow-y: auto;
        padding: 2px 0;
        scrollbar-width: thin;
        scrollbar-color: #2a2d38 transparent;
      }
      .va-composer-input::placeholder { color: rgba(160,165,190,0.5); }

      .va-mic-btn, .va-send-btn {
        flex-shrink: 0;
        width: 36px;
        height: 36px;
        border-radius: 10px;
        border: 1px solid rgba(255,255,255,0.1);
        background: rgba(30,34,46,0.5);
        color: rgba(180,185,210,0.8);
        display: grid;
        place-items: center;
        cursor: pointer;
        transition: background 150ms ease, color 150ms ease, border-color 150ms ease;
      }
      .va-mic-btn:hover, .va-send-btn:hover {
        background: rgba(149,128,255,0.18);
        border-color: rgba(149,128,255,0.4);
        color: #e8e6ff;
      }
      .va-send-btn { background: rgba(149,128,255,0.2); border-color: rgba(149,128,255,0.4); color: #c5bfff; }
      .va-send-btn:hover { background: rgba(149,128,255,0.35); }

      .va-mic-icon.hidden, .va-listen-dot.hidden, .va-send-btn.hidden { display: none; }
      .va-mic-icon { display: flex; }

      .va-listen-dot {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        background: #ff5050;
        animation: va-pulse 1s ease-in-out infinite;
      }
      @keyframes va-pulse {
        0%, 100% { transform: scale(1); opacity: 1; }
        50%       { transform: scale(1.4); opacity: 0.7; }
      }
      @media (prefers-reduced-motion: reduce) {
        .va-listen-dot { animation: none; }
      }
    `,document.head.appendChild(e)}}const re=[{code:"auto",label:"Auto-detect (follow user)"},{code:"en",label:"English"},{code:"ar",label:"Arabic"},{code:"bn",label:"Bengali"},{code:"cs",label:"Czech"},{code:"de",label:"German"},{code:"es",label:"Spanish"},{code:"fa",label:"Persian / Farsi"},{code:"fr",label:"French"},{code:"gu",label:"Gujarati"},{code:"hi",label:"Hindi"},{code:"id",label:"Indonesian"},{code:"it",label:"Italian"},{code:"ja",label:"Japanese"},{code:"ko",label:"Korean"},{code:"mr",label:"Marathi"},{code:"nl",label:"Dutch"},{code:"pa",label:"Punjabi"},{code:"pl",label:"Polish"},{code:"pt",label:"Portuguese"},{code:"ru",label:"Russian"},{code:"ta",label:"Tamil"},{code:"te",label:"Telugu"},{code:"tr",label:"Turkish"},{code:"ur",label:"Urdu"},{code:"zh",label:"Chinese (Mandarin)"}],oe=["hey_jarvis","alexa","hey_mycroft","hey_rhasspy"],z=[{id:"brain",labelKey:"tab.brain"},{id:"voice",labelKey:"tab.voice"},{id:"audio",labelKey:"tab.audio"},{id:"identity",labelKey:"tab.identity"},{id:"privacy",labelKey:"tab.privacy"}],ne={anthropic:"https://www.anthropic.com/legal/privacy",openai:"https://openai.com/policies/privacy-policy",gemini:"https://policies.google.com/privacy",ollama:"https://ollama.com/privacy"};class le{el;saveHandler=async()=>({ok:!0});currentCfg=null;activeTab="brain";constructor(e){this.el=document.createElement("aside"),this.el.className="va-settings",this.el.setAttribute("aria-modal","true"),this.el.setAttribute("role","dialog"),this.el.setAttribute("aria-label","Settings"),this.el.innerHTML=`
      <div class="va-settings-backdrop"></div>
      <div class="va-settings-panel">
        <header class="va-settings-header">
          <h2 class="va-settings-title">${o("settings.title")}</h2>
          <button data-close type="button" aria-label="${o("settings.close")}" class="va-settings-close">×</button>
        </header>
        <div class="va-settings-body">
          <!-- Vertical tab bar -->
          <nav class="va-tab-nav" role="tablist" aria-label="Settings sections">
            ${z.map(t=>`
              <button role="tab" id="va-tab-btn-${t.id}" data-tab="${t.id}" type="button"
                class="va-tab-btn${t.id===this.activeTab?" is-active":""}"
                aria-selected="${t.id===this.activeTab}"
                aria-controls="va-tab-${t.id}">
                ${o(t.labelKey)}
              </button>
            `).join("")}
          </nav>
          <!-- Tab panels -->
          <div class="va-tab-panels">
            ${z.map(t=>`<div role="tabpanel" id="va-tab-${t.id}" data-panel="${t.id}" class="va-tab-panel${t.id===this.activeTab?" is-active":""}" aria-labelledby="va-tab-btn-${t.id}"></div>`).join("")}
          </div>
        </div>
        <div data-error class="hidden va-settings-error"></div>
        <!-- AI Act footer disclosure -->
        <p data-ai-footer class="va-settings-ai-footer"></p>
        <footer class="va-settings-footer">
          <button data-cancel type="button" class="va-btn va-btn--ghost">${o("settings.cancel")}</button>
          <button data-save   type="button" class="va-btn va-btn--primary">${o("settings.save")}</button>
        </footer>
      </div>
    `,e.appendChild(this.el),this._wireEvents(),this._injectStyles(),this._buildPanels()}open(e){this.currentCfg=e,this._populate(e),this.el.classList.add("is-open"),document.body.style.overflow="hidden"}close(){this.el.classList.remove("is-open"),document.body.style.overflow=""}onSave(e){this.saveHandler=e}_wireEvents(){this.el.querySelector("[data-close]").addEventListener("click",()=>this.close()),this.el.querySelector("[data-cancel]").addEventListener("click",()=>this.close()),this.el.querySelector(".va-settings-backdrop").addEventListener("click",()=>this.close()),this.el.querySelectorAll("[data-tab]").forEach(e=>{e.addEventListener("click",()=>this._switchTab(e.dataset.tab))}),this.el.querySelector("[data-save]").addEventListener("click",async()=>{const e=this._read(),t=this.el.querySelector("[data-error]"),a=await this.saveHandler(e);a.ok?(t.classList.add("hidden"),this.close()):(t.textContent=(a.errors||["Save failed"]).join(" · "),t.classList.remove("hidden"))})}_switchTab(e){this.activeTab=e,this.el.querySelectorAll("[data-tab]").forEach(t=>{const a=t.dataset.tab===e;t.classList.toggle("is-active",a),t.setAttribute("aria-selected",String(a))}),this.el.querySelectorAll("[data-panel]").forEach(t=>{t.classList.toggle("is-active",t.dataset.panel===e)})}_buildPanels(){this._buildBrainPanel(),this._buildVoicePanel(),this._buildAudioPanel(),this._buildIdentityPanel(),this._buildPrivacyPanel()}_buildBrainPanel(){const e=this._panel("brain");e.innerHTML=`
      <div class="va-field">
        <label class="va-label">Provider</label>
        <select data-field="provider" class="va-select">
          <option value="anthropic">Anthropic Claude</option>
          <option value="openai">OpenAI GPT</option>
          <option value="gemini">Google Gemini</option>
          <option value="ollama">Ollama (local)</option>
        </select>
      </div>
      <div class="va-field">
        <label class="va-label">Model</label>
        <select data-field="model" class="va-select"></select>
      </div>
      <div data-secret-row class="va-field">
        <label class="va-label flex-row">
          <span data-secret-label>API key</span>
          <span data-saved-badge class="hidden va-badge-saved">✓ saved</span>
        </label>
        <div class="va-input-wrap">
          <input data-field="secret" type="password" class="va-input" placeholder="sk-…" />
          <button type="button" data-toggle-secret aria-label="Show or hide key" class="va-eye-btn">
            <svg data-eye-show width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
            <svg data-eye-hide class="hidden" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>
          </button>
        </div>
        <p class="va-hint" data-secret-hint>Stored in ~/.voice-assistant/.env, mode 0600.</p>
      </div>
      <div class="va-field">
        <label class="va-label">Reply language</label>
        <select data-field="respond_in" class="va-select">
          ${re.map(t=>`<option value="${t.code}">${t.label}</option>`).join("")}
        </select>
        <p class="va-hint">Override auto-detection and always reply in this language.</p>
      </div>
    `,e.querySelector('[data-field="provider"]').addEventListener("change",()=>{this._refreshSecretFields(),this._refreshModelOptions()}),e.querySelector("[data-toggle-secret]").addEventListener("click",()=>{const t=e.querySelector('[data-field="secret"]'),a=e.querySelector("[data-eye-show]"),s=e.querySelector("[data-eye-hide]"),r=t.type==="text";t.type=r?"password":"text",a.classList.toggle("hidden",!r),s.classList.toggle("hidden",r)})}_buildVoicePanel(){const e=this._panel("voice");e.innerHTML=`
      <div class="va-field">
        <label class="va-label">Avatar</label>
        <div data-field="avatar" class="va-avatar-grid"></div>
      </div>
      <div class="va-field">
        <label class="va-label">Voice</label>
        <select data-field="voice" class="va-select"></select>
        <button type="button" data-test-voice class="va-link-btn mt-2">&#9654; Test this voice</button>
      </div>
      <div class="va-field">
        <label class="va-label">Speech recognition language</label>
        <select data-field="stt_language" class="va-select"></select>
      </div>
    `}_buildAudioPanel(){const e=this._panel("audio");e.innerHTML=`
      <div class="va-field">
        <label class="va-label">Trigger</label>
        <div class="va-radio-group">
          <label class="va-radio-label">
            <input type="radio" name="audio_trigger" value="hotkey" checked> Hotkey
          </label>
          <label class="va-radio-label">
            <input type="radio" name="audio_trigger" value="wake_word"> Wake word
          </label>
        </div>
      </div>
      <div data-hotkey-row class="va-field">
        <label class="va-label">Hotkey</label>
        <input data-field="hotkey" class="va-input" placeholder="ctrl+shift+space" />
      </div>
      <div data-wake-row class="va-field hidden">
        <label class="va-label">Wake word</label>
        <select data-field="wake_word" class="va-select">
          ${oe.map(s=>`<option value="${s}">${s.replace(/_/g," ")}</option>`).join("")}
        </select>
      </div>
      <div data-sensitivity-row class="va-field hidden">
        <label class="va-label">Sensitivity: <span data-sensitivity-val>0.5</span></label>
        <input data-field="wake_sensitivity" type="range" min="0" max="1" step="0.05" value="0.5" class="va-range" />
        <p class="va-hint">Higher = fewer false positives but easier to miss.</p>
      </div>
    `,e.querySelectorAll('[name="audio_trigger"]').forEach(s=>{s.addEventListener("change",()=>this._refreshAudioTrigger(e))});const t=e.querySelector('[data-field="wake_sensitivity"]'),a=e.querySelector("[data-sensitivity-val]");t.addEventListener("input",()=>{a.textContent=t.value})}_buildIdentityPanel(){const e=this._panel("identity");e.innerHTML=`
      <div class="va-field">
        <label class="va-label">Your name</label>
        <input data-field="user_name" class="va-input" placeholder="(leave blank to skip)" />
      </div>
      <div class="va-field">
        <label class="va-label">How should the assistant address you?</label>
        <select data-field="user_address_as" class="va-select">
          <option value="none">Don't address me by name</option>
          <option value="first_name">By my first name</option>
          <option value="full_name">By my full name</option>
          <option value="title">By a title (Sir / Ma'am / etc)</option>
        </select>
      </div>
      <div data-title-row class="va-field hidden">
        <label class="va-label">Title</label>
        <input data-field="user_title" class="va-input" placeholder="Sir" />
      </div>
    `,e.querySelector('[data-field="user_address_as"]').addEventListener("change",()=>{this._refreshTitleRow(e)})}_buildPrivacyPanel(){const e=this._panel("privacy");e.innerHTML=`
      <div class="va-field">
        <label class="va-label">${o("allowed_folders.label")}</label>
        <input data-field="roots" class="va-input" placeholder="~" />
        <p class="va-hint">${o("allowed_folders.hint")}</p>
      </div>
      <!-- Display group -->
      <div class="va-section-divider"></div>
      <p class="va-section-heading">${o("display.group")}</p>
      <div class="va-field">
        <label class="va-label va-label--checkbox">
          <input data-field="display_hc" type="checkbox" />
          ${o("display.high_contrast")}
        </label>
      </div>
      <div class="va-field">
        <label class="va-label" for="display-font-size">${o("display.font_size")}</label>
        <select data-field="display_font_size" id="display-font-size" class="va-select">
          <option value="small">${o("display.font_small")}</option>
          <option value="medium" selected>${o("display.font_medium")}</option>
          <option value="large">${o("display.font_large")}</option>
          <option value="xl">${o("display.font_xl")}</option>
        </select>
      </div>
    `}_populate(e){this.currentCfg=e;const t=this._panel("brain");t.querySelector('[data-field="provider"]').value=e.provider,t.querySelector('[data-field="respond_in"]').value=e.respond_in||"auto",this._refreshModelOptions(),this._refreshSecretFields(),this._refreshVoiceSection();const a=this._panel("audio"),s=e.audio_trigger||"hotkey";a.querySelectorAll('[name="audio_trigger"]').forEach(b=>{b.checked=b.value===s}),a.querySelector('[data-field="hotkey"]').value=e.hotkey,a.querySelector('[data-field="wake_word"]').value=e.wake_word||"hey_jarvis";const r=e.wake_sensitivity??.5,n=a.querySelector('[data-field="wake_sensitivity"]');n.value=String(r),a.querySelector("[data-sensitivity-val]").textContent=String(r),this._refreshAudioTrigger(a);const p=this._panel("identity");p.querySelector('[data-field="user_name"]').value=e.user_name||"",p.querySelector('[data-field="user_address_as"]').value=e.user_address_as||"none",p.querySelector('[data-field="user_title"]').value=e.user_title||"",this._refreshTitleRow(p);const u=this._panel("privacy");u.querySelector('[data-field="roots"]').value=e.allowed_roots.join(", "),u.querySelector('[data-field="display_hc"]').checked=e.display_theme==="hc",u.querySelector('[data-field="display_font_size"]').value=e.display_font_size??"medium";const v=this.el.querySelector("[data-ai-footer]"),l=e.provider,d=ne[l]??"#";v.innerHTML=`AI assistant powered by <strong>${l}</strong>. Inputs are sent to <a href="${d}" target="_blank" rel="noopener noreferrer" class="va-ai-footer-link">${l} privacy policy</a>.`}_refreshAudioTrigger(e){const t=e.querySelector('[name="audio_trigger"]:checked')?.value||"hotkey";e.querySelector("[data-hotkey-row]").classList.toggle("hidden",t!=="hotkey"),e.querySelector("[data-wake-row]").classList.toggle("hidden",t!=="wake_word"),e.querySelector("[data-sensitivity-row]").classList.toggle("hidden",t!=="wake_word")}_refreshTitleRow(e){const t=e.querySelector('[data-field="user_address_as"]').value;e.querySelector("[data-title-row]").classList.toggle("hidden",t!=="title")}_refreshModelOptions(){const e=this._panel("brain"),t=e.querySelector('[data-field="provider"]').value,a=e.querySelector('[data-field="model"]'),s=this.currentCfg?.available_models?.[t]??[],r=this.currentCfg?.model;a.innerHTML="";const n=new Set;for(const p of s)n.add(p),a.appendChild(this._opt(p));r&&!n.has(r)&&a.appendChild(this._opt(r+" (custom)",r)),r&&(a.value=r)}_refreshSecretFields(){const e=this._panel("brain"),t=e.querySelector('[data-field="provider"]').value,a=e.querySelector("[data-secret-label]"),s=e.querySelector('[data-field="secret"]'),r=e.querySelector("[data-secret-hint]"),n=e.querySelector("[data-saved-badge]"),p=e.querySelector("[data-eye-show]"),u=e.querySelector("[data-eye-hide]");a.textContent=t==="ollama"?"Ollama base URL":"API key",s.value="",s.type=t==="ollama"?"text":"password",p.classList.remove("hidden"),u.classList.add("hidden");const v=t===this.currentCfg?.provider&&this.currentCfg?.has_secret===!0;n.classList.toggle("hidden",!v),t==="ollama"?(s.placeholder=this.currentCfg?.ollama_base_url||"http://localhost:11434",r.textContent="URL of your local Ollama instance."):v?(s.placeholder="✓ key on file — leave blank to keep current",r.textContent="Stored in ~/.voice-assistant/.env, mode 0600. Type a new key only to replace it."):(s.placeholder=t==="anthropic"?"sk-ant-…":t==="openai"?"sk-…":"AIza…",r.textContent="Stored in ~/.voice-assistant/.env, mode 0600.")}_refreshVoiceSection(){const e=this._panel("voice"),t=this.currentCfg?.available_avatars??["aria","liam","sage"],a=e.querySelector('[data-field="avatar"]');a.innerHTML="";for(const l of t){const d=document.createElement("button");d.type="button",d.className="va-avatar-btn",d.dataset.avatar=l;const b=l===(this.currentCfg?.avatar??"aria");d.setAttribute("aria-pressed",String(b)),b&&d.classList.add("is-selected"),d.innerHTML=`<img src="avatars/${l}.svg" alt="${l}" class="va-avatar-img" /><p class="va-avatar-name">${l}</p>`,d.addEventListener("click",()=>{a.querySelectorAll(".va-avatar-btn").forEach(y=>{y.setAttribute("aria-pressed","false"),y.classList.remove("is-selected")}),d.setAttribute("aria-pressed","true"),d.classList.add("is-selected")}),a.appendChild(d)}const s=this.currentCfg?.available_voices??[],r=e.querySelector('[data-field="voice"]');r.innerHTML="";const n={};for(const l of s)(n[l.language]??=[]).push(l);const p=Object.keys(n).sort((l,d)=>l==="en"?-1:d==="en"?1:l.localeCompare(d));for(const l of p){const d=document.createElement("optgroup"),y=n[l][0].label.match(/\(([^)]+)\)/);d.label=y?y[1]:l==="en"?"English":l;for(const f of n[l])d.appendChild(this._opt(f.notes?`${f.label} · ${f.notes}`:f.label,f.id));r.appendChild(d)}this.currentCfg?.voice&&(r.value=this.currentCfg.voice);const u=this.currentCfg?.available_stt_languages??[],v=e.querySelector('[data-field="stt_language"]');v.innerHTML="";for(const l of u)v.appendChild(this._opt(l.label,l.code));this.currentCfg?.stt_language&&(v.value=this.currentCfg.stt_language)}_read(){const e=this._panel("brain"),t=this._panel("voice"),a=this._panel("audio"),s=this._panel("identity"),r=this._panel("privacy"),n=e.querySelector('[data-field="provider"]').value,p=e.querySelector('[data-field="model"]').value.trim(),u=e.querySelector('[data-field="secret"]').value.trim(),v=e.querySelector('[data-field="respond_in"]').value,l=t.querySelector('[data-field="voice"]')?.value||this.currentCfg?.voice||"piper:en_US-amy-medium",d=t.querySelector('[data-field="stt_language"]')?.value||this.currentCfg?.stt_language||"auto",y=t.querySelector('[data-field="avatar"] [aria-pressed="true"]')?.dataset.avatar??this.currentCfg?.avatar??"aria",M=a.querySelector('[name="audio_trigger"]:checked')?.value||"hotkey",I=a.querySelector('[data-field="hotkey"]').value.trim()||"ctrl+shift+space",R=a.querySelector('[data-field="wake_word"]').value||"hey_jarvis",j=parseFloat(a.querySelector('[data-field="wake_sensitivity"]').value||"0.5"),N=s.querySelector('[data-field="user_name"]').value.trim()||null,O=s.querySelector('[data-field="user_address_as"]').value,D=s.querySelector('[data-field="user_title"]').value.trim()||null,V=r.querySelector('[data-field="roots"]').value.split(",").map(K=>K.trim()).filter(Boolean),F=r.querySelector('[data-field="display_hc"]').checked,Y=r.querySelector('[data-field="display_font_size"]').value,T={provider:n,model:p,hotkey:I,allowed_roots:V,ollama_base_url:n==="ollama"?u||this.currentCfg?.ollama_base_url||"http://localhost:11434":null,user_name:N,user_address_as:O,user_title:D,respond_in:v,voice:l,stt_language:d,avatar:y,audio_trigger:M,wake_word:R,wake_sensitivity:j,display_theme:F?"hc":"default",display_font_size:Y??"medium",locale:this.currentCfg?.locale,transparency_acknowledged:this.currentCfg?.transparency_acknowledged};return n!=="ollama"&&u&&(T._secret=u),T}_panel(e){return this.el.querySelector(`[data-panel="${e}"]`)}_opt(e,t){const a=document.createElement("option");return a.textContent=e,a.value=t??e,a}_injectStyles(){if(document.querySelector("#va-settings-style"))return;const e=document.createElement("style");e.id="va-settings-style",e.textContent=`
      .va-settings {
        position: fixed;
        inset: 0;
        z-index: 40;
        pointer-events: none;
        opacity: 0;
        transition: opacity 200ms ease;
      }
      .va-settings.is-open {
        pointer-events: auto;
        opacity: 1;
      }
      .va-settings-backdrop {
        position: absolute;
        inset: 0;
        background: rgba(0,0,0,0.45);
        backdrop-filter: blur(2px);
      }
      .va-settings-panel {
        position: absolute;
        top: 0; right: 0; bottom: 0;
        width: min(480px, 100vw);
        background: rgba(16, 18, 28, 0.96);
        backdrop-filter: blur(20px);
        border-left: 1px solid rgba(255,255,255,0.08);
        display: flex;
        flex-direction: column;
        transform: translateX(40px);
        transition: transform 200ms cubic-bezier(0.2, 0.8, 0.2, 1);
      }
      .va-settings.is-open .va-settings-panel { transform: translateX(0); }

      .va-settings-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        height: 52px;
        padding: 0 18px;
        border-bottom: 1px solid rgba(255,255,255,0.07);
        flex-shrink: 0;
      }
      .va-settings-title { font-size: 0.875rem; font-weight: 600; color: #e8e8f0; }
      .va-settings-close {
        width: 32px; height: 32px;
        display: grid; place-items: center;
        border-radius: 8px; border: none;
        background: transparent; color: rgba(200,200,220,0.5);
        font-size: 1.2rem; cursor: pointer;
        transition: background 150ms ease, color 150ms ease;
      }
      .va-settings-close:hover { background: rgba(255,255,255,0.06); color: #e8e8f0; }

      .va-settings-body {
        display: flex;
        flex: 1;
        min-height: 0;
        overflow: hidden;
      }

      /* Vertical tab nav */
      .va-tab-nav {
        display: flex;
        flex-direction: column;
        width: 100px;
        border-right: 1px solid rgba(255,255,255,0.06);
        padding: 10px 0;
        flex-shrink: 0;
        gap: 2px;
      }
      .va-tab-btn {
        padding: 10px 14px;
        font-size: 0.78rem;
        font-weight: 500;
        text-align: start;
        background: transparent;
        border: none;
        color: rgba(180,185,210,0.6);
        cursor: pointer;
        border-radius: 0;
        transition: background 150ms ease, color 150ms ease;
      }
      .va-tab-btn:hover { background: rgba(255,255,255,0.04); color: rgba(200,205,230,0.9); }
      .va-tab-btn.is-active {
        color: #c5bfff;
        background: rgba(149,128,255,0.1);
      }

      /* Tab panels */
      .va-tab-panels { flex: 1; overflow-y: auto; padding: 18px 16px; }
      .va-tab-panel { display: none; flex-direction: column; gap: 16px; }
      .va-tab-panel.is-active { display: flex; }

      /* Form fields */
      .va-field { display: flex; flex-direction: column; gap: 5px; }
      .va-label { font-size: 0.75rem; font-weight: 500; color: rgba(180,185,210,0.7); }
      .va-label.flex-row { display: flex; align-items: center; justify-content: space-between; }
      .va-input, .va-select {
        height: 38px;
        padding: 0 10px;
        border-radius: 8px;
        border: 1px solid rgba(255,255,255,0.1);
        background: rgba(20,24,36,0.8);
        color: #dde0f0;
        font: inherit;
        font-size: 0.83rem;
        outline: none;
        transition: border-color 150ms ease;
      }
      .va-input:focus, .va-select:focus { border-color: rgba(149,128,255,0.5); }
      .va-hint { font-size: 0.7rem; color: rgba(160,165,190,0.5); margin: 0; }
      .va-input-wrap { position: relative; }
      .va-input-wrap .va-input { width: 100%; padding-right: 42px; }
      .va-eye-btn {
        position: absolute; right: 2px; top: 2px;
        height: 34px; width: 38px;
        display: grid; place-items: center;
        border: none; background: transparent;
        color: rgba(160,165,190,0.5); cursor: pointer;
        border-radius: 6px;
        transition: color 150ms ease;
      }
      .va-eye-btn:hover { color: #dde0f0; }
      .va-badge-saved { font-size: 0.68rem; color: #5be080; font-weight: 600; }

      /* Avatar grid */
      .va-avatar-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; }
      .va-avatar-btn {
        border-radius: 10px; border: 2px solid rgba(255,255,255,0.08);
        padding: 8px; background: rgba(20,24,36,0.6);
        cursor: pointer; transition: border-color 150ms ease;
      }
      .va-avatar-btn:hover { border-color: rgba(149,128,255,0.3); }
      .va-avatar-btn.is-selected { border-color: #9580ff; }
      .va-avatar-img { width: 56px; height: 56px; border-radius: 50%; display: block; margin: 0 auto; }
      .va-avatar-name { font-size: 0.68rem; text-align: center; margin-top: 4px; text-transform: capitalize; color: rgba(180,185,210,0.7); }

      /* Radio group */
      .va-radio-group { display: flex; gap: 16px; }
      .va-radio-label { display: flex; align-items: center; gap: 6px; font-size: 0.83rem; color: rgba(180,185,210,0.8); cursor: pointer; }
      .va-radio-label input[type="radio"] { accent-color: #9580ff; }

      /* Range */
      .va-range { width: 100%; accent-color: #9580ff; }

      .va-link-btn { background: none; border: none; color: rgba(149,128,255,0.8); font-size: 0.75rem; cursor: pointer; padding: 0; }
      .va-link-btn:hover { color: #9580ff; text-decoration: underline; }
      .mt-2 { margin-top: 6px; }

      /* Footer */
      .va-settings-footer {
        display: flex; justify-content: flex-end; gap: 8px;
        padding: 14px 18px;
        border-top: 1px solid rgba(255,255,255,0.07);
        flex-shrink: 0;
      }
      .va-btn {
        height: 36px; padding: 0 16px;
        border-radius: 8px; font: inherit;
        font-size: 0.82rem; font-weight: 600;
        cursor: pointer; transition: opacity 150ms ease, background 150ms ease;
      }
      .va-btn--ghost {
        background: transparent;
        border: 1px solid rgba(255,255,255,0.1);
        color: rgba(180,185,210,0.8);
      }
      .va-btn--ghost:hover { background: rgba(255,255,255,0.05); }
      .va-btn--primary { background: #9580ff; border: none; color: #0b0d10; }
      .va-btn--primary:hover { opacity: 0.88; }

      .va-settings-error {
        padding: 8px 18px;
        font-size: 0.78rem;
        color: #ff8080;
        border-top: 1px solid rgba(255,255,255,0.05);
      }
      .va-settings-error.hidden { display: none; }

      /* AI Act footer */
      .va-settings-ai-footer {
        padding: 6px 18px;
        font-size: 0.68rem;
        color: rgba(160,165,190,0.45);
        border-top: 1px solid rgba(255,255,255,0.04);
        margin: 0;
      }
      .va-ai-footer-link {
        color: rgba(149,128,255,0.6);
        text-decoration: none;
      }
      .va-ai-footer-link:hover { text-decoration: underline; }

      /* Display section divider */
      .va-section-divider {
        height: 1px;
        background: rgba(255,255,255,0.07);
        margin: 4px 0;
      }
      .va-section-heading {
        font-size: 0.68rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: rgba(180,185,210,0.4);
        margin: 0;
      }
      /* Checkbox label */
      .va-label--checkbox {
        display: flex;
        align-items: center;
        gap: 8px;
        cursor: pointer;
        font-size: 0.83rem;
        color: rgba(180,185,210,0.8);
      }
      .va-label--checkbox input[type="checkbox"] { accent-color: #9580ff; }

      /* RTL: flip the active-tab indicator from left to inline-start */
      .va-tab-btn {
        border-inline-start: 2px solid transparent;
        border-left: none;
      }
      .va-tab-btn.is-active { border-inline-start-color: #9580ff; }

      /* High-contrast overrides */
      [data-theme="hc"] {
        --color-bg: #000;
        --color-fg: #fff;
        --color-surface: #1a1a1a;
        --color-border: #fff;
        --color-accent: #ffd400;
      }
      [data-theme="hc"] .va-settings-panel,
      [data-theme="hc"] .va-transparency-panel {
        background: #1a1a1a;
        border-color: #fff;
        color: #fff;
      }
      [data-theme="hc"] .va-input,
      [data-theme="hc"] .va-select {
        background: #000;
        color: #fff;
        border-color: #fff;
      }
      [data-theme="hc"] .va-btn--primary {
        background: #ffd400;
        color: #000;
      }
    `,document.head.appendChild(e)}}class de{el;timer=null;constructor(e){this.el=document.createElement("div"),this.el.className="fixed top-16 left-1/2 -translate-x-1/2 px-4 py-2 rounded-md text-sm font-medium opacity-0 pointer-events-none transition-opacity duration-200 z-40",e.appendChild(this.el)}show(e,t){this.timer!==null&&clearTimeout(this.timer);const a={info:"bg-surface border border-border text-fg",warn:"bg-warn/10 border border-warn/40 text-warn",error:"bg-warn/10 border border-warn/40 text-warn"};this.el.className=`fixed top-16 left-1/2 -translate-x-1/2 px-4 py-2 rounded-md text-sm font-medium opacity-100 transition-opacity duration-200 z-40 ${a[e]}`,this.el.textContent=t,this.timer=window.setTimeout(()=>{this.el.classList.replace("opacity-100","opacity-0")},4e3)}}class ce{el;listEl;constructor(e){this.el=document.createElement("aside"),this.el.className="va-history-panel",this.el.setAttribute("aria-label","Conversation history"),this.el.innerHTML=`
      <div class="va-history-header">
        <span class="va-history-title">${o("history.title")}</span>
      </div>
      <div class="va-history-list"></div>
    `,e.appendChild(this.el),this.listEl=this.el.querySelector(".va-history-list"),this._injectStyles()}populate(e){if(this.listEl.innerHTML="",e.length===0){const a=document.createElement("p");a.className="va-history-empty",a.textContent=o("history.empty"),this.listEl.appendChild(a);return}let t=0;for(const a of e)if(a.speaker==="user"){t++;const s=document.createElement("button");s.className="va-history-item",s.type="button",s.dataset.turnIndex=String(t),s.textContent=this._truncate(a.text,60),s.title=a.text,s.addEventListener("click",()=>this._scrollToTurn(t)),this.listEl.appendChild(s)}}_scrollToTurn(e){const t=document.querySelector(`[data-turn-id="turn-${e}"]`);t&&(t.scrollIntoView({behavior:"smooth",block:"start"}),t.classList.add("va-turn-highlight"),setTimeout(()=>t.classList.remove("va-turn-highlight"),1200))}_truncate(e,t){return e.length<=t?e:e.slice(0,t-1)+"…"}destroy(){this.el.remove()}_injectStyles(){if(document.querySelector("#va-history-style"))return;const e=document.createElement("style");e.id="va-history-style",e.textContent=`
      .va-history-panel {
        display: none; /* hidden on narrow viewports */
        flex-direction: column;
        width: 220px;
        min-width: 180px;
        max-width: 260px;
        border-right: 1px solid rgba(255,255,255,0.07);
        background: rgba(11,13,16,0.5);
        backdrop-filter: blur(8px);
        overflow: hidden;
      }
      @media (min-width: 1024px) {
        .va-history-panel { display: flex; }
      }
      .va-history-header {
        display: flex;
        align-items: center;
        height: 48px;
        padding: 0 14px;
        border-bottom: 1px solid rgba(255,255,255,0.06);
        flex-shrink: 0;
      }
      .va-history-title {
        font-size: 0.7rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: rgba(200,200,220,0.5);
      }
      .va-history-list {
        flex: 1;
        overflow-y: auto;
        padding: 6px 0;
        scrollbar-width: thin;
        scrollbar-color: #2a2d38 transparent;
      }
      .va-history-item {
        display: block;
        width: 100%;
        padding: 7px 14px;
        font-size: 0.75rem;
        line-height: 1.4;
        text-align: start;
        color: rgba(200,205,220,0.7);
        background: transparent;
        border: none;
        cursor: pointer;
        border-radius: 0;
        transition: background 150ms ease, color 150ms ease;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
      .va-history-item:hover {
        background: rgba(149,128,255,0.12);
        color: #e8e6ff;
      }
      .va-history-empty {
        padding: 14px;
        font-size: 0.75rem;
        color: rgba(200,200,220,0.35);
        text-align: center;
      }
      .va-turn-highlight {
        outline: 2px solid rgba(149,128,255,0.5);
        outline-offset: -2px;
        border-radius: 12px;
        transition: outline 0.2s ease;
      }
    `,document.head.appendChild(e)}}class pe{el;_visible=!1;constructor(e){this.el=document.createElement("div"),this.el.className="va-transparency-modal",this.el.setAttribute("role","dialog"),this.el.setAttribute("aria-modal","true"),this.el.setAttribute("aria-labelledby","va-transparency-title"),this.el.setAttribute("aria-describedby","va-transparency-body"),this.el.innerHTML=`
      <div class="va-transparency-backdrop"></div>
      <div class="va-transparency-panel" role="document">
        <h2 id="va-transparency-title" class="va-transparency-title"></h2>
        <p  id="va-transparency-body"  class="va-transparency-body"></p>
        <footer class="va-transparency-footer">
          <button data-ok type="button" class="va-btn va-btn--primary va-transparency-ok"></button>
        </footer>
      </div>
    `,e.appendChild(this.el),this._injectStyles()}show(e,t){if(this._visible)return;this._visible=!0;const a=this.el.querySelector("#va-transparency-title"),s=this.el.querySelector("#va-transparency-body"),r=this.el.querySelector("[data-ok]");a.textContent=o("transparency.title"),s.textContent=o("transparency.body"),r.textContent=o("transparency.ok"),this.el.classList.add("is-open"),document.body.style.overflow="hidden",r.focus();const n=async()=>{this.el.classList.remove("is-open"),document.body.style.overflow="",this._visible=!1,await t()};r.onclick=()=>{n()}}_injectStyles(){if(document.querySelector("#va-transparency-style"))return;const e=document.createElement("style");e.id="va-transparency-style",e.textContent=`
      .va-transparency-modal {
        position: fixed;
        inset: 0;
        z-index: 60;
        pointer-events: none;
        opacity: 0;
        transition: opacity 200ms ease;
      }
      .va-transparency-modal.is-open {
        pointer-events: auto;
        opacity: 1;
      }
      .va-transparency-backdrop {
        position: absolute;
        inset: 0;
        background: rgba(0,0,0,0.7);
        backdrop-filter: blur(4px);
      }
      .va-transparency-panel {
        position: absolute;
        top: 50%; left: 50%;
        transform: translate(-50%, -50%);
        width: min(480px, 90vw);
        background: rgba(16, 18, 28, 0.98);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 16px;
        padding: 28px 24px 20px;
        display: flex;
        flex-direction: column;
        gap: 16px;
      }
      .va-transparency-title {
        font-size: 1rem;
        font-weight: 700;
        color: #e8e8f0;
        margin: 0;
      }
      .va-transparency-body {
        font-size: 0.875rem;
        line-height: 1.6;
        color: rgba(200,205,220,0.85);
        margin: 0;
      }
      .va-transparency-footer {
        display: flex;
        justify-content: flex-end;
      }
      .va-transparency-ok {
        min-width: 120px;
      }
    `,document.head.appendChild(e)}}class ue{listeners=[];emit(e){for(const t of this.listeners)t(e)}on(e){return this.listeners.push(e),()=>{this.listeners=this.listeners.filter(t=>t!==e)}}}const _=new ue;window.va={emit:i=>_.emit(i)};const h=()=>typeof window<"u"&&typeof window.pywebview<"u",g={startListening:async()=>h()?window.pywebview.api.start_listening():void 0,stopListening:async()=>h()?window.pywebview.api.stop_listening():void 0,sendText:async i=>h()?window.pywebview.api.send_text(i):void 0,getConfig:async()=>h()?window.pywebview.api.get_config():{provider:"anthropic",model:"claude-sonnet-4-6",hotkey:"ctrl+shift+space",allowed_roots:["~"],ollama_base_url:null},saveConfig:async i=>h()?window.pywebview.api.save_config(i):{ok:!0},getHistory:async()=>h()?window.pywebview.api.get_history():[],quit:async()=>h()?window.pywebview.api.quit():void 0};h()?document.addEventListener("pywebviewready",()=>{g.getConfig().then(i=>_.emit({type:"config",cfg:i})),g.getHistory().then(i=>_.emit({type:"history_replay",items:i}))}):setTimeout(async()=>{const i=await g.getConfig();_.emit({type:"config",cfg:i})},100);const q=document.getElementById("app");q.className="va-app";q.innerHTML="";new U(document.body);const C=document.createElement("div");C.className="va-shell";q.appendChild(C);const ve=new ce(C),m=document.createElement("div");m.className="va-main";C.appendChild(m);const L=new W(m),w=new G(m,"aria"),$=new ie(m),x=new ae(m),P=new se(m),k=new le(document.body),he=new de(document.body),be=new pe(document.body);let c=null;function ye(i){const e=["ur","ar","he","fa"].includes(i);document.documentElement.dir=e?"rtl":"ltr",document.documentElement.lang=i||"en"}function ge(i){const e=document.documentElement;i.display_theme==="hc"?e.setAttribute("data-theme","hc"):e.removeAttribute("data-theme");const t={small:"87.5%",medium:"100%",large:"112.5%",xl:"125%"};e.style.fontSize=t[i.display_font_size??"medium"]??"100%"}(function(){if(document.querySelector("#va-layout-style"))return;const e=document.createElement("style");e.id="va-layout-style",e.textContent=`
    #app.va-app {
      height: 100vh;
      width: 100%;
      display: flex;
      flex-direction: column;
      position: relative;
      z-index: 1;
    }
    .va-shell {
      display: flex;
      flex: 1;
      min-height: 0;
      overflow: hidden;
    }
    .va-main {
      display: flex;
      flex-direction: column;
      flex: 1;
      min-width: 0;
      min-height: 0;
    }
    /* At ≥1024px: history sidebar visible */
    @media (min-width: 1024px) {
      .va-shell { flex-direction: row; }
    }
  `,document.head.appendChild(e)})();_.on(i=>{switch(i.type){case"status":L.setStatus(i.value),w.setState(i.value),i.value==="listening"?$.show():$.hide();break;case"transcript":x.push({speaker:i.speaker,text:i.text,tool_call:i.tool_call});break;case"transcript_start":i.speaker==="assistant"&&x.startAssistant();break;case"transcript_chunk":x.appendAssistant(i.text),L.setStatus("speaking"),w.setState("speaking");break;case"transcript_end":x.endAssistant();break;case"audio_level":w.setRms(i.rms);break;case"config":c=i.cfg,w.setAvatar(c.avatar??"aria");{const e=c.locale??"auto",t=e==="auto"?navigator.language?.split("-")[0]??"en":e;te(t);const a=c.respond_in==="auto"?c.user_address_language??t:c.respond_in??t;ye(a)}ge(c),c.transparency_acknowledged||be.show(c.provider,async()=>{const e={...c,transparency_acknowledged:!0};await g.saveConfig(e),c=e});break;case"toast":he.show(i.level,i.message);break;case"history_replay":x.replayHistory(i.items),ve.populate(i.items);break}});P.onSubmit(i=>{g.sendText(i)});P.onRecord(()=>{g.startListening()});L.onSettingsClick(()=>{c&&k.open(c)});k.onSave(async i=>g.saveConfig(i));document.addEventListener("keydown",i=>{const e=i.target,t=e&&(e.tagName==="INPUT"||e.tagName==="TEXTAREA"||e.tagName==="SELECT");if((i.metaKey||i.ctrlKey)&&i.key===","){i.preventDefault(),c&&k.open(c);return}if(i.key==="Escape"){k.close();return}if(!t){if(i.key==="/"){i.preventDefault(),document.querySelector("footer [data-input]")?.focus();return}if((i.metaKey||i.ctrlKey)&&i.key==="k"){i.preventDefault(),document.querySelector("footer [data-input]")?.focus();return}}});
