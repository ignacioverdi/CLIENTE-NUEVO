/* ═══════════════════════════════════════════════════════════════════════
   VIDEO EN VIVO CON DELAY — Receptor para la tablet (dentro de panel_voley).
   - Se conecta por WebRTC al emisor (camara.html) usando Firebase para señalizar.
   - Bufferea el video en memoria (MediaRecorder) y lo reproduce con retraso.
   - Delay configurable (0–25 s) + botón "último punto" (replay del rally cerrado).
   Requiere fbSet/fbGet (firebase.js) ya cargados en la página.
   ═══════════════════════════════════════════════════════════════════════ */
(function(){
  'use strict';

  /* Video: usa fbSet/fbGet de firebase.js, que firman con la sesion del usuario.
     Solo si no estuvieran cargados cae al acceso directo (compatibilidad). */
  function videoSet(path, value){
    if(typeof fbSet==='function'){ try{ return fbSet(path, value); }catch(e){} }
    try{ var u=(typeof FB_URL!=='undefined'?FB_URL:'https://nafels-voley-default-rtdb.firebaseio.com'); fetch(u+'/'+path+'.json',{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(value)}).catch(function(){}); }catch(e){}
  }
  function videoGet(path, cb){
    if(typeof fbGet==='function'){ try{ return fbGet(path, cb); }catch(e){} }
    try{ var u=(typeof FB_URL!=='undefined'?FB_URL:'https://nafels-voley-default-rtdb.firebaseio.com'); fetch(u+'/'+path+'.json').then(function(r){return r.json();}).then(function(d){cb(d);}).catch(function(){cb(null);}); }catch(e){ cb(null); }
  }


  var ICE = { iceServers:[ {urls:'stun:stun.l.google.com:19302'}, {urls:'stun:stun1.l.google.com:19302'} ] };

  var pc = null;
  var viewerId = null;
  var salaId = null;
  var liveStream = null;        /* stream directo recibido del emisor */
  var recorder = null;          /* MediaRecorder para el buffer con delay */
  var chunks = [];              /* {t, blob} buffer rodante */
  var BUFFER_MAX_MS = 40000;    /* guardamos hasta 40 s hacia atrás */
  var delayMs = 0;              /* delay actual: arranca en 0 (vivo directo) para ver imagen al instante */
  var playTimer = null;
  var connected = false;

  function $(id){ return document.getElementById(id); }

  /* ── conectar a una sala ── */
  function conectar(sala){
    if(connected) desconectar();
    salaId = String(sala).trim();
    viewerId = 'v'+Math.floor(Math.random()*1e9);
    setEstado('Conectando a la sala '+salaId+'…', 'wait');

    /* avisar al emisor que queremos conectarnos */
    videoSet('video_signal/'+salaId+'/requests/'+viewerId, { ts:Date.now() });

    pc = new RTCPeerConnection(ICE);
    var myCands = [];
    pc.onicecandidate = function(ev){
      if(ev.candidate){ myCands.push(ev.candidate.toJSON()); videoSet('video_signal/'+salaId+'/offer_cand/'+viewerId, myCands); }
    };
    pc.ontrack = function(ev){
      liveStream = ev.streams[0];
      onStreamRecibido(liveStream);
    };
    pc.onconnectionstatechange = function(){
      if(pc.connectionState==='connected'){ connected=true; setEstado('Conectado · en vivo', 'ok'); }
      else if(pc.connectionState==='failed'){ setEstado('No se pudo conectar. Revisá la sala y el WiFi.', 'err'); }
    };

    /* esperar la oferta del emisor */
    var tries=0;
    var wait = setInterval(function(){
      tries++;
      if(tries>40 || connected){ clearInterval(wait); if(!connected && tries>40) setEstado('El emisor no respondió. ¿La cámara está transmitiendo?', 'err'); return; }
      videoGet('video_signal/'+salaId+'/offer/'+viewerId, function(offer){
        if(offer && offer.sdp && !pc.currentRemoteDescription){
          pc.setRemoteDescription(new RTCSessionDescription(offer))
            .then(function(){ return pc.createAnswer(); })
            .then(function(ans){ return pc.setLocalDescription(ans).then(function(){ return ans; }); })
            .then(function(ans){ videoSet('video_signal/'+salaId+'/answer/'+viewerId, {type:ans.type, sdp:ans.sdp}); })
            .catch(function(e){ setEstado('Error al conectar: '+e.message, 'err'); });
        }
      });
      videoGet('video_signal/'+salaId+'/answer_cand/'+viewerId, function(cands){
        if(cands && Array.isArray(cands)){
          cands.forEach(function(c){ try{ pc.addIceCandidate(new RTCIceCandidate(c)); }catch(e){} });
        }
      });
    }, 800);
  }

  /* ═══════════════════════════════════════════════════════════════════
     GRABACIÓN EN CICLOS CERRADOS (para que cada clip sea REPRODUCIBLE).
     El MediaRecorder graba de a un ciclo completo (CICLO_MS). Al cerrarse,
     queda un video WebM válido con su encabezado → se puede reproducir fluido.
     Guardamos los últimos ciclos para delay y para "último punto".
     ═══════════════════════════════════════════════════════════════════ */
  var CICLO_MS = 12000;          /* cada clip dura 12 s */
  var MAX_CICLOS = 5;            /* guardamos los últimos 5 (~60 s hacia atrás) */
  var ciclos = [];              /* [{ini, fin, url, blob}] clips cerrados y reproducibles */
  var cicloBuf = [];            /* pedazos del ciclo en curso */
  var cicloIni = 0;
  var recTimer = null;
  var rallyMarks = [];          /* timestamps de fin de cada punto (del scout) */
  var _lastRally = -1;

  function onStreamRecibido(stream){
    var vLive = $('vd-live'), vDelay = $('vd-delay');
    if(vLive){
      vLive.srcObject = stream; vLive.muted = true; vLive.setAttribute('playsinline','');
      vLive.play().catch(function(){}); vLive.style.display='block';
    }
    if(vDelay){ vDelay.style.display='none'; }
    setEstado('Conectado · en vivo', 'ok');
    iniciarGrabacionEnCiclos(stream);
    escucharCierreDeRally();
  }

  /* graba de a ciclos completos; cada ciclo cerrado es un video reproducible */
  function iniciarGrabacionEnCiclos(stream){
    ciclos = []; cicloBuf = [];
    var mime = (window.MediaRecorder && MediaRecorder.isTypeSupported('video/webm;codecs=vp8')) ? 'video/webm;codecs=vp8'
             : (window.MediaRecorder && MediaRecorder.isTypeSupported('video/webm') ? 'video/webm' : '');
    function nuevoCiclo(){
      if(!stream || !stream.active) return;
      cicloBuf = []; cicloIni = Date.now();
      var rec;
      try{ rec = new MediaRecorder(stream, mime?{mimeType:mime}:undefined); }
      catch(e){ return; }
      rec.ondataavailable = function(e){ if(e.data && e.data.size>0) cicloBuf.push(e.data); };
      rec.onstop = function(){
        if(cicloBuf.length){
          var blob = new Blob(cicloBuf, {type:'video/webm'});
          var url = URL.createObjectURL(blob);
          ciclos.push({ ini:cicloIni, fin:Date.now(), url:url, blob:blob });
          while(ciclos.length>MAX_CICLOS){ var viejo=ciclos.shift(); try{ URL.revokeObjectURL(viejo.url); }catch(e){} }
        }
        /* arrancar el siguiente ciclo enseguida */
        if(connected) nuevoCiclo();
      };
      rec.start();
      recorder = rec;
      /* cerrar este ciclo a los CICLO_MS */
      recTimer = setTimeout(function(){ try{ if(rec.state!=='inactive') rec.stop(); }catch(e){} }, CICLO_MS);
    }
    nuevoCiclo();
  }

  /* escuchar cuándo el scout cierra un punto (voley_live.rally sube) */
  function escucharCierreDeRally(){
    if(_ralloTimer) clearInterval(_ralloTimer);
    _ralloTimer = setInterval(function(){
      videoGet('voley_live', function(d){
        if(d && typeof d.rally==='number'){
          if(_lastRally<0){ _lastRally=d.rally; return; }
          if(d.rally>_lastRally){
            _lastRally = d.rally;
            rallyMarks.push(Date.now());   /* acá terminó un punto */
            if(rallyMarks.length>20) rallyMarks.shift();
            var b=$('vd-replay-hint'); if(b){ b.style.display='block'; setTimeout(function(){ b.style.display='none'; },3000); }
          }
        }
      });
    }, 1500);
  }
  var _ralloTimer = null;

  /* ── DELAY CONTINUO: reproducir el ciclo anterior (ya cerrado y fluido) ── */
  function setDelay(seg){
    delayMs = Math.max(0, seg*1000);
    var lbl = $('vd-delay-lbl'); if(lbl) lbl.textContent = seg+' s';
    var vLive=$('vd-live'), vDelay=$('vd-delay');
    if(seg<=0){
      if(playTimer){ clearInterval(playTimer); playTimer=null; }
      if(vLive) vLive.style.display='block';
      if(vDelay){ vDelay.style.display='none'; vDelay.onended=null; }
      setEstado('En vivo', 'ok');
      return;
    }
    setEstado('Delay '+seg+' s · preparando…', 'wait');
    if(playTimer) clearInterval(playTimer);
    /* reproducir en cadena los ciclos ya cerrados, con el atraso pedido */
    playTimer = setInterval(reproducirDelay, 1500);
  }

  /* ── DELAY CONTINUO fluido, sin salto entre ciclos ──
     Un solo video visible. El truco anti-salto: precargamos el siguiente clip
     en un elemento oculto (queda en caché del navegador), así cuando el visible
     termina, el siguiente carga al instante (ya está en memoria). */
  var vdPrecarga = null;

  function _precargar(url){
    if(!url) return;
    if(!vdPrecarga){ vdPrecarga = document.createElement('video'); vdPrecarga.muted=true; vdPrecarga.preload='auto'; vdPrecarga.style.display='none'; }
    if(vdPrecarga.src !== url){ vdPrecarga.src = url; vdPrecarga.load(); }
  }

  function reproducirDelay(){
    if(delayMs<=0) return;
    var vDelay=$('vd-delay'), vLive=$('vd-live');
    if(!vDelay || !ciclos.length) return;
    /* si ya está reproduciendo, no interrumpir */
    if(vDelay.style.display==='block' && !vDelay.paused && !vDelay.ended) return;
    var objetivo = Date.now() - delayMs;
    var idx = -1;
    for(var i=0;i<ciclos.length;i++){ if(ciclos[i].ini<=objetivo && ciclos[i].fin>=objetivo){ idx=i; break; } }
    if(idx<0) idx = 0;
    if(!ciclos[idx]) return;
    if(vLive) vLive.style.display='none';
    vDelay.style.display='block';
    _reproducirCiclo(idx);
  }

  /* reproduce el ciclo idx y encadena con el siguiente al terminar */
  function _reproducirCiclo(idx){
    var v = $('vd-delay');
    if(!v || !ciclos[idx]) return;
    v.srcObject=null;
    v.muted=true; v.setAttribute('playsinline','');
    v.oncanplay = function(){ var p=v.play(); if(p&&p.catch) p.catch(function(){ setTimeout(function(){ if(v.paused) v.play().catch(function(){}); },200); }); };
    v.src = ciclos[idx].url;
    v.load();
    setEstado('Delay '+(delayMs/1000)+' s', 'ok');
    /* precargar el siguiente para que el cambio sea instantáneo */
    if(ciclos[idx+1]) _precargar(ciclos[idx+1].url);
    v.onended = function(){
      if(ciclos[idx+1]){ _reproducirCiclo(idx+1); }
      else {
        /* alcanzamos el presente: seguir con el ciclo más nuevo que aparezca */
        var espera = setInterval(function(){
          if(ciclos[idx+1]){ clearInterval(espera); _reproducirCiclo(idx+1); }
          else if(delayMs<=0){ clearInterval(espera); }
        }, 500);
      }
    };
  }

  function reproducirClip(url, onended){
    var vDelay=$('vd-delay');
    if(!vDelay) return;
    vDelay.srcObject=null;
    vDelay.muted=true;
    vDelay.setAttribute('playsinline','');
    vDelay.onended = function(){ if(onended) try{ onended(); }catch(e){} };
    var intentado=false;
    function arrancar(){
      if(intentado) return; intentado=true;
      var p = vDelay.play();
      if(p && p.catch) p.catch(function(){ intentado=false; setTimeout(function(){ if(vDelay.paused) vDelay.play().catch(function(){}); }, 300); });
    }
    vDelay.oncanplay = arrancar;
    vDelay.onloadeddata = arrancar;
    vDelay.src=url;
    vDelay.load();
    setTimeout(function(){ if(vDelay.paused) arrancar(); }, 500);
  }

  /* ── ÚLTIMO PUNTO: reproducir el clip que contiene el último rally cerrado ── */
  function replayUltimoPunto(segAntes){
    var vDelay=$('vd-delay'), vLive=$('vd-live');
    if(!ciclos.length){ setEstado('Todavía no hay video grabado.', 'wait'); return; }
    /* momento del último punto (si el scout lo marcó); si no, "ahora - 10s" */
    var momento = rallyMarks.length ? rallyMarks[rallyMarks.length-1] : (Date.now()-10000);
    /* buscar el ciclo que contiene ese momento */
    var elegido=null;
    for(var i=0;i<ciclos.length;i++){ if(ciclos[i].ini<=momento && ciclos[i].fin>=momento){ elegido=ciclos[i]; break; } }
    if(!elegido) elegido = ciclos[ciclos.length-1];   /* el más reciente cerrado */
    if(!elegido){ setEstado('El punto todavía se está grabando, probá en un segundo.', 'wait'); return; }

    if(playTimer){ clearInterval(playTimer); playTimer=null; }   /* pausar el delay mientras vemos el replay */
    var lbl=$('vd-estado-replay'); if(lbl) lbl.style.display='block';
    if(vLive) vLive.style.display='none';
    vDelay.style.display='block';
    reproducirClip(elegido.url, function(){
      if(lbl) lbl.style.display='none';
      /* volver a vivo tras el replay */
      if(vLive) vLive.style.display='block';
      vDelay.style.display='none';
    });
  }

  function desconectar(){
    connected=false;
    if(playTimer){ clearInterval(playTimer); playTimer=null; }
    if(recTimer){ clearTimeout(recTimer); recTimer=null; }
    if(_ralloTimer){ clearInterval(_ralloTimer); _ralloTimer=null; }
    if(recorder && recorder.state!=='inactive'){ try{ recorder.stop(); }catch(e){} }
    recorder=null;
    if(pc){ try{ pc.close(); }catch(e){} pc=null; }
    if(salaId && viewerId){ videoSet('video_signal/'+salaId+'/requests/'+viewerId, null); }
    ciclos.forEach(function(c){ try{ URL.revokeObjectURL(c.url); }catch(e){} });
    ciclos=[]; cicloBuf=[]; rallyMarks=[]; _lastRally=-1; liveStream=null;
    var vLive=$('vd-live'), vDelay=$('vd-delay');
    if(vLive){ vLive.srcObject=null; vLive.style.display='none'; }
    if(vDelay){ vDelay.src=''; vDelay.srcObject=null; vDelay.style.display='none'; }
    setEstado('Desconectado.', '');
  }

  function setEstado(msg, cls){
    var el=$('vd-estado'); if(!el) return;
    el.textContent=msg; el.className='vd-estado'+(cls?' '+cls:'');
  }

  window.VideoDelay = {
    conectar: conectar,
    desconectar: desconectar,
    setDelay: setDelay,
    replayUltimoPunto: replayUltimoPunto,
    estaConectado: function(){ return connected; }
  };
})();
