// static/widget.js  (Django static or serv from CDN)
(function () {
  const s = document.currentScript;
  const EMBED_ID = s.dataset.embedId;
  console.log(EMBED_ID)
  const API_BASE = s.dataset.apiBase || new URL(s.src).origin; // data-api-base
  // parent page URL (about:srcdoc/invalid then no send)
  function getParentUrl() {
    try {
      const href = window.location.href;
      if (/^https?:\/\//i.test(href)) return href;
      if (/^https?:\/\//i.test(document.referrer)) return document.referrer;
    } catch (_) {}
    return "";
  }
  const PARENT_URL = getParentUrl();

  // Small debug
  console.debug("[AVA] API_BASE:", API_BASE, "EMBED_ID:", EMBED_ID, "PARENT_URL:", PARENT_URL || "(none)");


  console.debug(`${API_BASE}/api/widget/${EMBED_ID}/config/`)

  const uuidLike = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
  if (!EMBED_ID || !uuidLike.test(EMBED_ID)) {
    console.error("[AVA] Invalid or missing embed_id. Provide a valid UUID in data-embed-id.");
    return;
  }



  // —— Launcher (bottom-right)
  const btn = document.createElement("div");
  btn.style.cssText =
    "position:fixed;right:20px;bottom:20px;width:56px;height:56px;border-radius:50%;" +
    "box-shadow:0 8px 24px rgba(0,0,0,.2);cursor:pointer;display:flex;align-items:center;justify-content:center;" +
    "background:#1f7aec;color:#fff;font:600 14px/1 Inter,sans-serif;z-index:999999";
  btn.textContent = "Chat";
  document.body.appendChild(btn);

  // —— Chat iframe
  const frame = document.createElement("iframe");
  frame.setAttribute("scrolling", "no"); // outer scrollbar hide
  frame.style.cssText =
    "position:fixed;right:20px;bottom:90px;width:360px;height:520px;border:0;border-radius:16px;" +
    "box-shadow:0 12px 40px rgba(0,0,0,.22);display:none;z-index:999999;background:#fff";
  document.body.appendChild(frame);

  // Toggle open/close
  btn.onclick = () => {
    frame.style.display = frame.style.display === "none" ? "block" : "none";
  };
  // Minimize message from iframe
  window.addEventListener("message", (e) => {
    if (e?.data?.type === "AVA_MINIMIZE") frame.style.display = "none";
  });

  // —— Session id
  const sidKey = "ava_sid";
  const sessionId =
    localStorage.getItem(sidKey) ||
    Date.now() + "-" + Math.random().toString(36).slice(2);
  localStorage.setItem(sidKey, sessionId);

  // —— Fetch public config then mount UI
  fetch(`${API_BASE}/api/widget/${EMBED_ID}/config/`)
    .then((r) => r.json())
    .then((cfg) => {
      console.log(cfg)
      const AGENT_NAME = cfg.data.agentName || "AVA";
      const BUSINESS_NAME = cfg.data.businessName || "";
      const LOGO_URL = cfg.data.logoUrl || null;

      console.log(AGENT_NAME)

      const html = `
      <html>
      <head>
        <meta charset="utf-8">
        <style>
          *{box-sizing:border-box}
          html,body{height:100%;overflow:hidden}
          body{
            margin:0;display:flex;flex-direction:column;height:100%;
            font-family:Inter,system-ui,-apple-system,Segoe UI,Roboto,sans-serif;background:#fff;color:#111827
          }
          .head{
            display:flex;gap:10px;align-items:center;padding:12px;border-bottom:1px solid #eee;position:relative
          }
          .title{font-weight:700;font-size:14px}
          .sub{color:#6b7280;font-weight:500;font-size:12px}
          .logo{width:28px;height:28px;border-radius:50%;object-fit:cover}
          .close{
            position:absolute;right:8px;top:8px;width:28px;height:28px;border:0;background:#f3f4f6;color:#111827;
            border-radius:8px;cursor:pointer;font-weight:700
          }
          .close:hover{background:#e5e7eb}
          .log{
            flex:1;overflow:auto;padding:12px;font-size:14px;background:#fff
          }
          /* hide scrollbar but allow scroll */
          .log::-webkit-scrollbar{width:0;height:0}
          .log{-ms-overflow-style:none;scrollbar-width:none}

          .row{display:flex;margin:8px 0}
          .row.user{justify-content:flex-end}
          .row.bot{justify-content:flex-start}
          .bubble{
            max-width:75%;padding:10px 12px;border-radius:12px;white-space:pre-wrap;line-height:1.35;word-break:break-word
          }
          .row.user .bubble{background:#1f7aec;color:#fff;border-top-right-radius:4px}
          .row.bot .bubble{background:#f1f5f9;color:#111827;border-top-left-radius:4px}
          .who{font-size:11px;color:#6b7280;margin:0 4px 4px 4px}

          form.send{display:flex;gap:8px;padding:12px;border-top:1px solid #eee}
          .inp{flex:1;padding:10px;border:1px solid #e5e7eb;border-radius:10px;outline:none}
          .btn{padding:10px 14px;border:0;background:#1f7aec;color:#fff;border-radius:10px;cursor:pointer}
          .btn:disabled{opacity:.6;cursor:not-allowed}
        </style>
      </head>
      <body>
        <div class="head">
          ${LOGO_URL ? `<img src="${LOGO_URL}" class="logo" alt="logo">` : ""}
          <div>
            <div class="title">${AGENT_NAME}</div>
            <div class="sub">${BUSINESS_NAME}</div>
          </div>
          <button class="close" id="ava_close" aria-label="Minimize">×</button>
        </div>

        <div id="log" class="log" role="log" aria-live="polite"></div>

        <form id="f" class="send" novalidate>
          <input id="inp" class="inp" placeholder="Type your message..." autocomplete="off" />
          <button id="sendBtn" class="btn" type="submit" aria-label="Send">Send</button>
        </form>

        <script>
          const API_BASE   = ${JSON.stringify(API_BASE)};
          const EMBED_ID   = ${JSON.stringify(EMBED_ID)};
          const SID        = ${JSON.stringify(sessionId)};
          const AGENT_NAME = ${JSON.stringify(AGENT_NAME)};
          const SOURCE_URL = ${JSON.stringify(PARENT_URL)}; // valid http(s) then send

          const log = document.getElementById('log');
          const form = document.getElementById('f');
          const inp = document.getElementById('inp');
          const sendBtn = document.getElementById('sendBtn');
          const closeBtn = document.getElementById('ava_close');

          function bubble(text, who){
            const row = document.createElement('div'); row.className = 'row ' + (who==='user' ? 'user' : 'bot');
            const wrap = document.createElement('div');
            const whoLbl = document.createElement('div'); whoLbl.className='who'; whoLbl.textContent = (who==='user' ? 'You' : AGENT_NAME);
            const b = document.createElement('div'); b.className='bubble'; b.textContent = text || '';
            wrap.appendChild(whoLbl); wrap.appendChild(b); row.appendChild(wrap);
            log.appendChild(row); log.scrollTop = log.scrollHeight;
          }

          closeBtn.addEventListener('click', ()=>{ try { parent.postMessage({ type: 'AVA_MINIMIZE' }, '*'); } catch(e){} });

          let convId = null, ready = false, pendingText = null;

          async function start(){
            const payload = { embed_id: EMBED_ID, session_id: SID };
            if (SOURCE_URL) payload.source_url = SOURCE_URL; // invalid then no send
            try {
              const r = await fetch(API_BASE + '/api/chat/start/', {
                method:'POST', headers:{'Content-Type':'application/json'},
                body: JSON.stringify(payload)
              });
              const j = await r.json().catch(()=>({}));
              if (!r.ok) {
                console.error('[AVA] start failed', r.status, j);
                bubble('Service unavailable.', 'bot');
                return;
              }
              convId = j.data.conversation_id; ready = true;
              bubble(j.data.message?.content || 'Hello! How can I help?', 'bot');
              if (pendingText) { sendCore(pendingText); pendingText = null; }
            } catch(err) {
              console.error('[AVA] start error', err);
              bubble('Network error.', 'bot');
            }
          }

          async function sendCore(text){
            try {
              sendBtn.disabled = true;
              const r = await fetch(API_BASE + '/api/chat/send/', {
                method:'POST', headers:{'Content-Type':'application/json'},
                body: JSON.stringify({ conversation_id: convId, text })
              });
              const j = await r.json().catch(()=>({}));
              if (!r.ok) {
                console.error('[AVA] send failed', r.status, j);
                bubble(j.detail || 'Sorry, something went wrong.', 'bot');
              } else {
                bubble(j.data.reply || '...', 'bot');
              }
            } catch(err) {
              bubble('Network error. Please try again.', 'bot');
            } finally {
              sendBtn.disabled = false;
              inp.focus();
            }
          }

          function handleSubmit(e){
            e && e.preventDefault();
            const v = (inp.value || '').trim(); if (!v) return;
            bubble(v, 'user'); inp.value = '';
            if (!ready || !convId) pendingText = v; else sendCore(v);
          
          }

          form.addEventListener('submit', handleSubmit);
          inp.addEventListener('keydown', (e)=>{ if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSubmit(e); } });

          // end conversation on unload
          window.addEventListener('beforeunload', () => {
            if (!convId) return;
            const payload = new Blob([JSON.stringify({ conversation_id: convId })], { type:'application/json' });
            navigator.sendBeacon(API_BASE + '/api/chat/end/', payload);
          });

          start();
        <\/script>
      </body>
      </html>`;
      frame.srcdoc = html;
    })
    .catch((err) => console.error("AVA config error", err));
})();
