/* ============================================================================
   datos_seguros.js — abre los datos del club
   ----------------------------------------------------------------------------
   Los archivos de datos estan cifrados en el servidor. La llave vive en
   Firebase y solo la recibe quien inicio sesion. Este archivo:
     1) busca la llave (guardada en el dispositivo, o pidiendosela a Firebase)
     2) descifra los datos y los deja disponibles como siempre
   Para el resto de la app no cambia nada: window.PP_DATA, window.LIGA_DATA,
   etc. quedan igual que antes.
   ============================================================================ */
(function(){
  var GUARDADA = 'club_llave';

  function llaveLocal(){
    try{
      /* si paso el plazo sin confirmar contra el servidor, se descarta */
      if(typeof llaveVencida === 'function' && llaveVencida()){
        window.VB_LLAVE_VENCIDA = true;
        return '';
      }
      return localStorage.getItem(GUARDADA) || '';
    }catch(e){ return ''; }
  }

  /* SHA-256 sincronico y compacto (el mismo que usa el cifrador en Python) */
  function sha256(bytes){
    var K=[0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
           0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
           0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
           0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
           0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
           0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
           0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
           0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2];
    var H=[0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19];
    var l=bytes.length, bitLen=l*8;
    var t=new Uint8Array((((l+9)+63)>>6)<<6);
    t.set(bytes); t[l]=0x80;
    var dv=new DataView(t.buffer);
    dv.setUint32(t.length-4, bitLen>>>0, false);
    dv.setUint32(t.length-8, Math.floor(bitLen/4294967296), false);
    var w=new Int32Array(64);
    function rr(x,n){ return (x>>>n)|(x<<(32-n)); }
    for(var i=0;i<t.length;i+=64){
      for(var j=0;j<16;j++) w[j]=dv.getUint32(i+j*4,false);
      for(j=16;j<64;j++){
        var s0=rr(w[j-15],7)^rr(w[j-15],18)^(w[j-15]>>>3);
        var s1=rr(w[j-2],17)^rr(w[j-2],19)^(w[j-2]>>>10);
        w[j]=(w[j-16]+s0+w[j-7]+s1)|0;
      }
      var a=H[0],b=H[1],c=H[2],d=H[3],e=H[4],f=H[5],g=H[6],h=H[7];
      for(j=0;j<64;j++){
        var S1=rr(e,6)^rr(e,11)^rr(e,25), ch=(e&f)^(~e&g);
        var t1=(h+S1+ch+K[j]+w[j])|0;
        var S0=rr(a,2)^rr(a,13)^rr(a,22), mj=(a&b)^(a&c)^(b&c);
        var t2=(S0+mj)|0;
        h=g; g=f; f=e; e=(d+t1)|0; d=c; c=b; b=a; a=(t1+t2)|0;
      }
      H[0]=(H[0]+a)|0; H[1]=(H[1]+b)|0; H[2]=(H[2]+c)|0; H[3]=(H[3]+d)|0;
      H[4]=(H[4]+e)|0; H[5]=(H[5]+f)|0; H[6]=(H[6]+g)|0; H[7]=(H[7]+h)|0;
    }
    var out=new Uint8Array(32), o=new DataView(out.buffer);
    for(i=0;i<8;i++) o.setUint32(i*4, H[i]>>>0, false);
    return out;
  }

  function hexABytes(h){
    var a=new Uint8Array(h.length/2);
    for(var i=0;i<a.length;i++) a[i]=parseInt(h.substr(i*2,2),16);
    return a;
  }
  function contador(n){
    var b=new Uint8Array(8);
    for(var i=7;i>=0;i--){ b[i]=n & 255; n=Math.floor(n/256); }
    return b;
  }
  /* la llave propia de cada archivo (igual que en Python) */
  function claveArchivo(llaveHex, nombre){
    var k=hexABytes(llaveHex);
    var n=[]; var enc=unescape(encodeURIComponent(nombre));
    for(var i=0;i<enc.length;i++) n.push(enc.charCodeAt(i));
    var ent=new Uint8Array(k.length+1+n.length);
    ent.set(k); ent[k.length]=124; ent.set(n, k.length+1);   /* 124 = | */
    return sha256(ent);
  }

  function descifrar(b64, clave){
    var bin=atob(b64), largo=bin.length;
    var datos=new Uint8Array(largo);
    for(var i=0;i<largo;i++) datos[i]=bin.charCodeAt(i);
    var k=clave, bloque=0, pos=0;
    while(pos<largo){
      var ent=new Uint8Array(k.length+8);
      ent.set(k); ent.set(contador(bloque), k.length);
      var f=sha256(ent);
      for(var j=0;j<32 && pos<largo;j++,pos++) datos[pos]^=f[j];
      bloque++;
    }
    return new TextDecoder('utf-8').decode(datos);
  }

  /* abre todo lo que haya llegado cifrado */
  window.abrirDatos = function(){
    var llave = llaveLocal();
    if(!llave || !window.__D) return false;
    var abiertos = 0;
    for(var nombre in window.__D){
      try{
        (0, eval)(descifrar(window.__D[nombre], claveArchivo(llave, nombre)));
        abiertos++;
      }catch(e){
        try{ console.warn('[datos] no pude abrir', nombre); }catch(_){}
      }
    }
    return abiertos > 0;
  };

  /* Guarda la llave que llega de Firebase. Si es la primera vez, recarga
     para que las paginas arranquen ya con los datos abiertos. */
  /* ══ CUANTO DURA LA LLAVE GUARDADA ═══════════════════════════════════════
     La llave se guarda en el dispositivo para que la app funcione sin
     internet: en el gimnasio muchas veces no hay señal, y ese es el modo de
     uso normal, no la excepcion.

     Pero guardada para siempre significa que un club que dejo de pagar sigue
     usando todo mientras no borre los datos del navegador. Podrian ser meses.

     El equilibrio: la llave vale VB_DIAS_LLAVE dias desde la ultima vez que
     el servidor la confirmo. Sin internet la app sigue funcionando todo ese
     tiempo; con internet se renueva sola y el usuario nunca se entera. Pasado
     el plazo sin poder confirmar, deja de abrir los datos.

     30 dias es un buen punto: cubre de sobra una gira o un mes sin conexion,
     y acota la ventana de uso sin pagar a un mes. */
  var VB_DIAS_LLAVE = 30;
  var DESDE = 'club_llave_desde';

  function llaveVencida(){
    try{
      var d = parseInt(localStorage.getItem(DESDE) || '0', 10);
      if(!d) return false;              /* de antes de esta version: se respeta */
      return (Date.now() - d) > VB_DIAS_LLAVE * 86400000;
    }catch(e){ return false; }
  }

  window.guardarLlave = function(llave){
    if(!llave) return;
    var antes = llaveLocal();
    try{
      localStorage.setItem(GUARDADA, llave);
      /* cada confirmacion del servidor renueva el plazo */
      localStorage.setItem(DESDE, String(Date.now()));
    }catch(e){}
    if(!antes) location.reload();
  };

  window.olvidarLlave = function(){
    try{ localStorage.removeItem(GUARDADA); }catch(e){}
  };

  /* ══ El aviso del plan ═══════════════════════════════════════════════════
     Si la suscripcion vencio, la llave no llega y las pantallas quedan
     vacias. Sin explicacion eso parece un error del sistema y el cliente
     llama enojado; con el cartel entiende que tiene que renovar.

     Va aca porque este archivo lo carga TODA pantalla que muestre datos: se
     escribe una vez y aparece en las 53. */
  function _cartel(html, color){
    if(document.getElementById('vb-plan-aviso')) return;
    var d = document.createElement('div');
    d.id = 'vb-plan-aviso';
    d.style.cssText = 'position:fixed;left:0;right:0;bottom:0;z-index:9999;'
      + 'background:' + color + ';color:#fff;padding:11px 16px;font-size:14px;'
      + 'text-align:center;font-family:system-ui,sans-serif;line-height:1.4;'
      + 'box-shadow:0 -2px 14px rgba(0,0,0,.35)';
    d.innerHTML = html;
    document.body.appendChild(d);
  }

  function _avisarPlan(){
    if(!document.body) return;
    if(window.VB_PLAN_VENCIDO){
      _cartel('<b>La suscripción venció el ' + window.VB_PLAN_VENCIDO + '.</b> '
        + 'Los datos del club quedan sin acceso hasta renovarla. '
        + 'Escribinos y lo resolvemos en el momento.', '#b91c1c');
    } else if(window.VB_LLAVE_VENCIDA){
      _cartel('<b>Hace más de 30 días que la app no se conecta.</b> '
        + 'Abrila una vez con internet y vuelve a funcionar sin conexión.', '#b45309');
    } else if(window.VB_PLAN_VENCE_EN !== undefined){
      var d = window.VB_PLAN_VENCE_EN;
      _cartel('La suscripción vence en <b>' + d + (d === 1 ? ' día' : ' días')
        + '</b>. Escribinos para renovarla.', '#b45309');
    }
  }
  /* se revisa un rato despues, cuando ya llego la respuesta del servidor */
  if(document.readyState === 'loading'){
    document.addEventListener('DOMContentLoaded', function(){ setTimeout(_avisarPlan, 2500); });
  } else {
    setTimeout(_avisarPlan, 2500);
  }
})();
