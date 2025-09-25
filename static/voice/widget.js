(function(){
  const API_BASE = window.InsecticaVoice?.apiBase || "/api";
  let conversationId = null;
  let mediaRecorder = null;
  let chunks = [];
  let isRecording = false;

  async function startConversation(){
    const res = await fetch(`${API_BASE}/start/`, {method: 'POST'});
    const json = await res.json();
    conversationId = json.conversation_id;
  }

  function el(tag, attrs={}, children=[]){
    const e = document.createElement(tag);
    for (const [k,v] of Object.entries(attrs)) {
      if (k === 'class') e.className = v; else e.setAttribute(k,v);
    }
    (Array.isArray(children)?children:[children]).forEach(c=>{
      if (typeof c === 'string') e.appendChild(document.createTextNode(c));
      else if (c) e.appendChild(c);
    });
    return e;
  }

  async function recordToggle(btn, log, audioEl){
    if (!isRecording) {
      const stream = await navigator.mediaDevices.getUserMedia({audio: true});
      mediaRecorder = new MediaRecorder(stream, {mimeType: 'audio/webm'});
      chunks = [];
      mediaRecorder.ondataavailable = (e)=>{ if (e.data.size>0) chunks.push(e.data); };
      mediaRecorder.onstop = async ()=>{
        const blob = new Blob(chunks, {type: 'audio/webm'});
        const form = new FormData();
        form.append('audio', blob, 'input.webm');
        form.append('duration_ms', 0);
        const res = await fetch(`${API_BASE}/conversations/${conversationId}/ingest_audio/`, {method:'POST', body: form});
        const json = await res.json();
        log.textContent = json.assistant_text || '(no text)';
        audioEl.src = json.assistant_audio_url;
        audioEl.play();
      };
      mediaRecorder.start();
      isRecording = true;
      btn.textContent = 'Stop & Send';
    } else {
      mediaRecorder.stop();
      isRecording = false;
      btn.textContent = 'Hold to Speak';
    }
  }

  async function init(){
    await startConversation();
    const root = document.getElementById('insectica-voice-root');
    const container = el('div', {class: 'insectica-voice'}, [
      el('style', {}, `
        .insectica-voice {font-family: system-ui, sans-serif; max-width: 360px; padding: 12px; border: 1px solid #e5e7eb; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,.05)}
        .iv-head {display:flex; align-items:center; gap:8px; margin-bottom: 8px}
        .iv-title {font-weight:700}
        .iv-log {min-height: 48px; padding: 8px; background:#f9fafb; border-radius: 8px; margin: 8px 0}
        .iv-cta {display:flex; gap:8px; align-items:center}
        .iv-btn {padding:10px 12px; border-radius: 9999px; border:0; background:#111827; color:white; cursor:pointer}
      `),
      el('div', {class:'iv-head'}, [
        el('div', {class:'iv-title'}, 'Insectica • Talk to Sara')
      ]),
      el('div', {class:'iv-log', id:'iv-log'}, 'Tap the mic and speak.'),
      el('div', {class:'iv-cta'}, [
        el('button', {class:'iv-btn', id:'iv-btn'}, 'Hold to Speak'),
        el('audio', {id:'iv-audio', controls:''})
      ])
    ]);
    root.appendChild(container);

    const btn = document.getElementById('iv-btn');
    const log = document.getElementById('iv-log');
    const audioEl = document.getElementById('iv-audio');

    btn.addEventListener('click', ()=> recordToggle(btn, log, audioEl));
    btn.addEventListener('mousedown', async ()=>{ if (!isRecording) await recordToggle(btn, log, audioEl); });
    btn.addEventListener('mouseup',   async ()=>{ if (isRecording) await recordToggle(btn, log, audioEl); });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
