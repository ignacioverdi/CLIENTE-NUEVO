(function(){

// ── CHAT IA VOLLEY NÄFELS — Self-contained widget ──────────────────
var CSS = [
  '#vb-chat-btn{position:fixed;bottom:24px;right:24px;width:58px;height:58px;border-radius:50%;border:none;cursor:pointer;z-index:9000;background:transparent;padding:0;filter:drop-shadow(0 5px 14px rgba(0,0,0,.5));transition:transform .2s,filter .2s}',
    '#vb-chat-btn img{width:100%;height:100%;display:block;object-fit:contain;pointer-events:none}',
  '#vb-chat-btn:hover{transform:scale(1.1) rotate(-8deg);filter:drop-shadow(0 6px 28px rgba(37,99,235,.8))}',
  '#vb-chat-dot{position:fixed;bottom:74px;right:22px;width:14px;height:14px;background:#E8192C;border-radius:50%;border:2px solid #07080F;z-index:9001;display:none;animation:vbPulse 1.5s infinite}',
  '@keyframes vbPulse{0%,100%{transform:scale(1)}50%{transform:scale(1.3)}}',
  '#vb-chat-panel{position:fixed;bottom:96px;right:24px;width:min(390px,calc(100vw - 32px));height:min(560px,calc(100vh - 110px));background:#0D0E1A;border:1px solid rgba(255,255,255,.14);border-radius:20px;z-index:9000;display:none;flex-direction:column;box-shadow:0 24px 80px rgba(0,0,0,.75);overflow:hidden;font-family:"Barlow Condensed","Segoe UI",sans-serif}',
  '#vb-chat-panel.vb-open{display:flex;animation:vbSlideUp .22s ease}',
  '@keyframes vbSlideUp{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:translateY(0)}}',
  '.vb-hdr{display:flex;align-items:center;gap:10px;padding:13px 16px;background:rgba(37,99,235,.08);border-bottom:1px solid rgba(255,255,255,.07);flex-shrink:0}',
  '.vb-hdr-ball{width:30px;height:30px;flex-shrink:0}',
  '.vb-hdr-info{flex:1}',
  '.vb-hdr-title{font-family:"Bebas Neue",sans-serif;font-size:15px;letter-spacing:2px;color:#fff}',
  '.vb-hdr-sub{font-size:10px;color:#64748b;display:flex;align-items:center;gap:5px;margin-top:1px}',
  '.vb-dot-g{width:6px;height:6px;background:#22c55e;border-radius:50%}',
  '.vb-close{background:rgba(255,255,255,.08);border:none;color:#94a3b8;width:30px;height:30px;border-radius:50%;cursor:pointer;font-size:14px;display:flex;align-items:center;justify-content:center;transition:all .15s}',
  '.vb-close:hover{background:rgba(255,255,255,.16);color:#fff}',
  '#vb-chat-msgs{flex:1;overflow-y:auto;padding:14px 14px 8px;display:flex;flex-direction:column;gap:10px;scrollbar-width:thin;scrollbar-color:rgba(255,255,255,.08) transparent}',
  '.vb-msg{display:flex;gap:8px;max-width:92%}',
  '.vb-msg.vb-user{flex-direction:row-reverse;align-self:flex-end}',
  '.vb-bubble{padding:10px 13px;border-radius:14px;font-size:13px;line-height:1.55;white-space:pre-wrap;word-break:break-word}',
  '.vb-msg.vb-bot .vb-bubble{background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.07);border-bottom-left-radius:4px;color:#e2e8f0}',
  '.vb-msg.vb-user .vb-bubble{background:linear-gradient(135deg,#1d4ed8,#2563eb);border-bottom-right-radius:4px;color:#fff}',
  '.vb-avatar{width:28px;height:28px;border-radius:50%;flex-shrink:0;display:flex;align-items:center;justify-content:center;font-size:14px;margin-top:2px;background:rgba(37,99,235,.12);border:1px solid rgba(37,99,235,.2)}',
  '.vb-typing{display:flex;gap:4px;align-items:center;padding:10px 13px}',
  '.vb-typing span{width:7px;height:7px;background:#64748b;border-radius:50%;animation:vbBounce .9s infinite;display:block}',
  '.vb-typing span:nth-child(2){animation-delay:.15s}',
  '.vb-typing span:nth-child(3){animation-delay:.3s}',
  '@keyframes vbBounce{0%,60%,100%{transform:translateY(0)}30%{transform:translateY(-7px)}}',
  '#vb-suggestions{padding:6px 12px 8px;display:flex;gap:5px;flex-wrap:wrap;border-top:1px solid rgba(255,255,255,.06);flex-shrink:0;background:rgba(0,0,0,.15)}',
  '.vb-sugg{background:rgba(37,99,235,.08);border:1px solid rgba(37,99,235,.2);color:#93c5fd;border-radius:20px;padding:4px 11px;font-size:11px;font-family:"Barlow Condensed","Segoe UI",sans-serif;font-weight:700;cursor:pointer;transition:all .15s}',
  '.vb-sugg:hover{background:rgba(37,99,235,.2);color:#fff}',
  '.vb-input-row{display:flex;gap:8px;padding:10px 12px;border-top:1px solid rgba(255,255,255,.07);flex-shrink:0;background:rgba(0,0,0,.2)}',
  '#vb-input{flex:1;background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.14);color:#e2e8f0;padding:9px 12px;border-radius:12px;font-family:"Barlow Condensed","Segoe UI",sans-serif;font-size:13px;outline:none;transition:border-color .15s;resize:none;height:40px;min-height:40px;max-height:110px}',
  '#vb-input:focus{border-color:rgba(37,99,235,.5)}',
  '#vb-input::placeholder{color:#475569}',
  '#vb-send{width:40px;height:40px;border-radius:12px;border:none;background:linear-gradient(135deg,#1d4ed8,#2563eb);color:#fff;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:all .15s;flex-shrink:0}',
  '#vb-send:hover{transform:scale(1.05)}',
  '#vb-send:disabled{opacity:.38;cursor:not-allowed;transform:none}'
].join('\n');

// (datos en vivo: ver vbLoadData mas abajo)


var vbOpen=false, vbLoading=false, vbHistory=[];
var LANG=(function(){try{var l=localStorage.getItem('vb_lang');if(l)return l;}catch(e){}var n=(navigator.language||'es').substring(0,2).toLowerCase();return['es','en','de'].indexOf(n)>=0?n:'es';})();

// Inject CSS
var styleEl=document.createElement('style');
styleEl.textContent=CSS;
document.head.appendChild(styleEl);

// Inject HTML
var wrapEl=document.createElement('div');
wrapEl.innerHTML=[
  '<div id="vb-chat-dot"></div>',
  '<button id="vb-chat-btn" onclick="vbToggle()" title="Asistente IA">',
  /* La pelota del club, con el fondo recortado. Va embebida acá para no
     depender de ningún archivo suelto del repo. */
  '<img src="data:image/png;base64,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" alt="" draggable="false"></button>',
  '<div id="vb-chat-panel">',
  '<div class="vb-hdr">',
  '<svg class="vb-hdr-ball" viewBox="0 0 30 30" xmlns="http://www.w3.org/2000/svg"><circle cx="15" cy="15" r="14" fill="#1e3a8a"/><circle cx="15" cy="15" r="13" fill="#dbeafe"/><path d="M2,8 Q5,3 10,2 Q12,6 8,11 Q5,9 2,8Z" fill="#1e3a8a" opacity=".9"/><path d="M16,2 Q21,4 24,8 Q20,11 16,8 Q16,5 16,2Z" fill="#1e3a8a" opacity=".9"/><path d="M5,20 Q8,24 14,24 Q15,20 12,17 Q9,18 5,20Z" fill="#1e3a8a" opacity=".9"/><g fill="none" stroke="#fbbf24" stroke-width="1.5" stroke-linecap="round"><path d="M10,2 Q14,7 15,6 Q18,4 16,2"/><path d="M16,2 Q15,8 18,11 Q21,10 24,8"/></g></svg>',
  '<div class="vb-hdr-info"><div class="vb-hdr-title">ASISTENTE NAFELS</div><div class="vb-hdr-sub"><div class="vb-dot-g"></div><span>IA aktiv</span></div></div>',
  '<button class="vb-close" onclick="vbToggle()">&#x2715;</button>',
  '</div>',
  '<div id="vb-chat-msgs"></div>',
  '<div id="vb-suggestions">',
  '<button class="vb-sugg" onclick="vbSugg(this)">\u00bfC\u00f3mo armo una rutina?</button>',
  '<button class="vb-sugg" onclick="vbSugg(this)">\u00bfC\u00f3mo cargo el wellness?</button>',
  '<button class="vb-sugg" onclick="vbSugg(this)">\u00bfQu\u00e9 es el EFF?</button>',
  '</div>',
  '<div class="vb-input-row">',
  '<textarea id="vb-input" placeholder="Pregunt\u00e1 sobre stats, t\u00e1ctica..." onkeydown="if(event.key===\'Enter\'&&!event.shiftKey){event.preventDefault();vbSend()}" oninput="vbResize(this)"></textarea>',
  '<button id="vb-send" onclick="vbSend()"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M22 2L11 13M22 2L15 22L11 13M11 13L2 9L22 2"/></svg></button>',
  '</div></div>'
].join('');
document.body.appendChild(wrapEl);

var SUGG={
  es:[['\u00bfQui\u00e9n ataca mejor?','Stats del equipo','\u00bfC\u00f3mo mejoro el EFF?'],
      ['\u00bfQu\u00e9 es Side Out?','Diferencia SO vs TR','\u00bfQu\u00e9 significan las zonas?']],
  en:[['Who attacks best?','Team stats','How to improve EFF?'],['What is Side Out?','SO vs TR','What do zones mean?']],
  de:[['Wer greift am besten an?','Team-Stats','Wie EFF verbessern?'],['Was ist Side Out?','SO vs TR','Was bedeuten Zonen?']]
};

function vbToggle(){
  vbOpen=!vbOpen;
  var p=document.getElementById('vb-chat-panel');
  if(vbOpen){
    p.classList.add('vb-open');
    document.getElementById('vb-chat-dot').style.display='none';
    if(!vbHistory.length) vbWelcome();
    setTimeout(function(){var i=document.getElementById('vb-input');if(i)i.focus();},280);
  } else { p.classList.remove('vb-open'); }
}

function vbWelcome(){
  var w={es:'\u00a1Hola! Soy el asistente de **Volley N\u00e4fels**. Te ayudo con stats, scouting y a usar el sistema (wellness, rutinas, pizarr\u00f3n...). \u00bfEn qu\u00e9 te doy una mano?',
         en:'Hi! I\'m the **Volley N\u00e4fels** assistant. I help with stats, scouting and using the system (wellness, routines, board...). How can I help?',
         de:'Hallo! Ich bin der **Volley N\u00e4fels** Assistent. Ich helfe bei Stats, Scouting und der Bedienung des Systems (Wellness, Pl\u00e4ne, Board...). Wie kann ich helfen?'};
  vbAdd('bot', w[LANG]||w.es);
}

function vbSend(){
  var input=document.getElementById('vb-input');
  var text=(input.value||'').trim();
  if(!text||vbLoading)return;
  input.value=''; vbResize(input);
  document.getElementById('vb-suggestions').style.display='none';
  vbAdd('user',text); vbCall(text);
}

function vbSugg(btn){
  var text=btn.textContent;
  document.getElementById('vb-suggestions').style.display='none';
  vbAdd('user',text); vbCall(text);
}

function vbLang(txt){
  if(/\b(wie|was|wer|ich|du|ist|sind|spieler|angriff|aufschlag|mannschaft|spiel)\b/i.test(txt))return 'de';
  if(/\b(what|how|who|is|are|player|attack|serve|team|game|the|and)\b/i.test(txt))return 'en';
  return 'es';
}

// ── CEREBRO LOCAL — sin API, lee los datos EN VIVO (nunca se desactualiza) ──
var DATA={players:null,teams:null,fixture:null,loaded:false,loading:null};
function vbLoadData(){
  if(DATA.loaded)return Promise.resolve();
  if(DATA.loading)return DATA.loading;
  DATA.loading=Promise.all([
    fetch('nla_full_stats.json').then(function(r){return r.json();}).then(function(j){DATA.players=(j&&j.players)||[];DATA.teams=(j&&j.teams)||[];}).catch(function(){DATA.players=DATA.players||[];DATA.teams=DATA.teams||[];}),
    fetch('proximo_rival.js').then(function(r){return r.text();}).then(function(tx){var m=tx.match(/=\s*(\{[\s\S]*\})\s*;/);if(m){try{DATA.fixture=JSON.parse(m[1]);}catch(e){}}}).catch(function(){})
  ]).then(function(){DATA.loaded=true;});
  return DATA.loading;
}
function vbNorm(s){return (s||'').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'');}
function vbFmt(n){return (n===null||n===undefined)?'-':(Math.round(n*10)/10);}

var KB={
 playbook:{
  es:'📘 **Team Playbook** — Es cómo juega el equipo, escrito. Está en el Hub.\n\nAdentro vas a encontrar: nuestra identidad y valores, los principios de juego, el sistema de ataque y de defensa, el bloqueo, qué buscamos con el saque y con la recepción, cómo manejamos el error, y el lenguaje común (los llamados y las señas).\n\nLo escribe el cuerpo técnico y lo lee todo el plantel. Si sos jugador lo ves pero no lo podés editar.\n\n💡 Si sos nuevo en el equipo, empezá por *Identidad* y *Lenguaje común*.',
  en:'📘 **Team Playbook** — How the team plays, written down. You will find it on the Hub.\n\nInside: our identity and values, playing principles, offensive and defensive systems, blocking, what we look for on serve and reception, how we handle errors, and the common language (calls and signals).\n\nThe coaching staff writes it, the whole squad reads it. As a player you can read it but not edit it.\n\n💡 New to the team? Start with *Identity* and *Common language*.',
  de:'📘 **Team Playbook** — Wie die Mannschaft spielt, schriftlich. Du findest es im Hub.\n\nInhalt: unsere Identität und Werte, Spielprinzipien, Angriffs- und Abwehrsystem, Block, was wir bei Aufschlag und Annahme suchen, Fehlermanagement und die gemeinsame Sprache (Rufe und Zeichen).\n\nDas Trainerteam schreibt es, das ganze Team liest es.\n\n💡 Neu im Team? Fang mit *Identität* und *Gemeinsame Sprache* an.'
 },
 calendario:{
  es:'📅 **Calendario** — Todos los partidos de la temporada, con fecha, hora, rival y si jugamos de local o visitante.\n\nTenés dos vistas: *Lista* (uno abajo del otro) y *Planificación* (en grilla por semana, quincena o mes).\n\nCada partido muestra el escudo del rival, y tocando el 📍 se abre la dirección en el mapa.\n\n💡 Los horarios de entrenamiento están aparte, en **Horarios**.',
  en:'📅 **Calendar** — Every match of the season: date, time, opponent and home/away.\n\nTwo views: *List* and *Planning* (grid by week, fortnight or month).\n\nEach match shows the opponent badge, and tapping 📍 opens the address on the map.\n\n💡 Training times are separate, under **Schedule**.',
  de:'📅 **Kalender** — Alle Spiele der Saison: Datum, Uhrzeit, Gegner und Heim/Auswärts.\n\nZwei Ansichten: *Liste* und *Planung* (Raster nach Woche, zwei Wochen oder Monat).\n\nJedes Spiel zeigt das Gegnerwappen; mit 📍 öffnet sich die Adresse auf der Karte.\n\n💡 Trainingszeiten stehen separat unter **Zeiten**.'
 },
 cortes:{
  es:'🎬 **Cortes de Video** — Mirás tus jugadas sin buscarlas en el video entero.\n\nElegís el equipo, el partido, la acción (saque, ataque, recepción…) y el jugador, y te arma la lista de clips. Apretás *Reproducir* y salta directo al segundo exacto de cada jugada.\n\nTenés *Loop* para repetir, y los botones de 2s para adelantar o retroceder.\n\n💡 Filtrá por valoración (por ejemplo sólo los `#`) para ver únicamente los puntos.',
  en:'🎬 **Video Clips** — Watch your actions without scrubbing the full video.\n\nPick team, match, action (serve, attack, reception…) and player, and it builds the clip list. Hit *Play* and it jumps to the exact second of each rally.\n\nThere is *Loop* to repeat, and 2s buttons to step back and forward.\n\n💡 Filter by evaluation (e.g. only `#`) to watch just the points.',
  de:'🎬 **Video-Clips** — Schau deine Aktionen, ohne das ganze Video zu durchsuchen.\n\nWähle Team, Spiel, Aktion (Aufschlag, Angriff, Annahme…) und Spieler — die Clip-Liste wird erstellt. *Play* springt direkt zur genauen Sekunde.\n\n*Loop* zum Wiederholen, 2s-Tasten zum Vor- und Zurückspringen.\n\n💡 Nach Bewertung filtern (z. B. nur `#`), um nur die Punkte zu sehen.'
 },
 heatmap:{
  es:'🔥 **Heat Maps** — La cancha pintada según dónde caen las pelotas.\n\nHay uno por fundamento: ataque, saque, recepción, defensa y distribución del armador. Cuanto más fuerte el color, más acciones en esa zona.\n\nSe pueden filtrar por jugador, por rival y por partido.\n\n💡 Sirven para ver tendencias: si siempre atacás a la misma zona, el rival lo va a leer.',
  en:'🔥 **Heat Maps** — The court coloured by where the ball lands.\n\nOne per skill: attack, serve, reception, defence and setter distribution. The stronger the colour, the more actions in that zone.\n\nFilterable by player, opponent and match.\n\n💡 Great for spotting patterns: if you always hit the same zone, the opponent will read it.',
  de:'🔥 **Heat Maps** — Das Feld eingefärbt nach Ballaufkommen.\n\nEine pro Element: Angriff, Aufschlag, Annahme, Abwehr und Zuspielverteilung. Je kräftiger die Farbe, desto mehr Aktionen in dieser Zone.\n\nFilterbar nach Spieler, Gegner und Spiel.\n\n💡 Ideal für Muster: Wer immer dieselbe Zone angreift, wird gelesen.'
 },
 baterias:{
  es:'⚡ **Baterías** — Series de trabajo para entrenar un fundamento puntual.\n\nSe arman desde el sistema y quedan guardadas. Cada una tiene su objetivo y su forma de puntuar, así podés ver si vas mejorando de una a otra.\n\n💡 Preguntale al cuerpo técnico cuál te toca esta semana.',
  en:'⚡ **Batteries** — Work series to train one specific skill.\n\nThey are built in the system and saved. Each has its goal and scoring, so you can see whether you improve from one to the next.\n\n💡 Ask the coaching staff which one is yours this week.',
  de:'⚡ **Batterien** — Übungsserien für ein bestimmtes Element.\n\nSie werden im System erstellt und gespeichert. Jede hat ihr Ziel und ihre Wertung, damit du den Fortschritt siehst.\n\n💡 Frag das Trainerteam, welche diese Woche dran ist.'
 },
 miperfil:{
  es:'📊 **Mi rendimiento** — Tus números, partido a partido y acumulados.\n\nVas a ver tu eficiencia en cada fundamento, comparada con el promedio del equipo. Verde es que estás por encima, rojo por debajo.\n\nEntrás desde el Hub o desde *Equipo* → tu tarjeta → *Stats*.\n\n💡 No mires un solo partido: la tendencia de varios dice mucho más.',
  en:'📊 **My performance** — Your numbers, per match and cumulative.\n\nYou see your efficiency in each skill compared to the team average. Green means above, red means below.\n\nOpen it from the Hub or from *Team* → your card → *Stats*.\n\n💡 Do not read one match alone: the trend across several says much more.',
  de:'📊 **Meine Leistung** — Deine Zahlen, pro Spiel und kumuliert.\n\nDu siehst deine Effizienz je Element im Vergleich zum Teamschnitt. Grün heisst darüber, Rot darunter.\n\nÜber den Hub oder *Team* → deine Karte → *Stats*.\n\n💡 Nicht ein einzelnes Spiel lesen: der Trend über mehrere sagt mehr.'
 },
 avisos:{
  es:'🔔 **Avisos** — El sistema te manda notificaciones al celular: convocatorias, cambios de horario, cuando hay video nuevo o cuando falta tu wellness.\n\nPara activarlos, entrá al Hub desde el celular y aceptá cuando te pregunte si querés recibir avisos. Si dijiste que no y te arrepentiste, hay que habilitarlos desde la configuración del navegador.\n\n💡 Llegan aunque tengas la app cerrada.',
  en:'🔔 **Alerts** — The system sends notifications to your phone: call-ups, schedule changes, new video, or a missing wellness entry.\n\nTo turn them on, open the Hub on your phone and accept when asked. If you declined and changed your mind, enable them in your browser settings.\n\n💡 They arrive even with the app closed.',
  de:'🔔 **Benachrichtigungen** — Das System schickt Meldungen aufs Handy: Aufgebote, Zeitänderungen, neue Videos oder fehlendes Wellness.\n\nZum Aktivieren den Hub auf dem Handy öffnen und zustimmen. Falls abgelehnt, in den Browser-Einstellungen erlauben.\n\n💡 Sie kommen auch bei geschlossener App an.'
 },
 sesion:{
  es:'🔐 **Ingreso** — Se entra una sola vez por dispositivo y después ya no te vuelve a pedir la clave.\n\nSi de golpe te la pide otra vez, es normal: el club puede cerrar las sesiones (por ejemplo si se perdió un celular). Entrás de nuevo con tu mail y tu clave y listo.\n\n💡 Si no te acordás la clave, pedísela al cuerpo técnico.',
  en:'🔐 **Access** — You log in once per device and it will not ask again.\n\nIf it suddenly asks again, that is normal: the club can close sessions (for example if a phone was lost). Just log in again with your email and password.\n\n💡 Forgot your password? Ask the coaching staff.',
  de:'🔐 **Zugang** — Einmal pro Gerät anmelden, danach fragt es nicht mehr.\n\nWenn plötzlich doch gefragt wird, ist das normal: der Club kann Sitzungen schliessen (z. B. bei verlorenem Handy). Einfach neu anmelden.\n\n💡 Passwort vergessen? Frag das Trainerteam.'
 },
 idioma:{
  es:'🌐 **Idioma** — Arriba a la derecha de cada pantalla tenés **ES · EN · DE**. Tocás el que quieras y toda la app cambia, incluido este chat.',
  en:'🌐 **Language** — Top right of every screen you have **ES · EN · DE**. Tap one and the whole app switches, including this chat.',
  de:'🌐 **Sprache** — Oben rechts auf jedem Bildschirm: **ES · EN · DE**. Antippen und die ganze App wechselt, auch dieser Chat.'
 },
 celular:{
  es:'📱 **En el celular** — Se usa desde el navegador, no hace falta bajar nada.\n\nPara tenerla como una app: abrila en el celular y usá *Agregar a pantalla de inicio* (en iPhone está en el botón de compartir; en Android, en el menú de los tres puntos).\n\n💡 Así te queda el ícono como cualquier otra app y arranca a pantalla completa.',
  en:'📱 **On your phone** — It runs in the browser, nothing to download.\n\nTo keep it like an app: open it on your phone and use *Add to Home Screen* (iPhone: share button; Android: three-dot menu).\n\n💡 You get an icon like any other app and it opens full screen.',
  de:'📱 **Auf dem Handy** — Läuft im Browser, nichts herunterzuladen.\n\nWie eine App: im Handy öffnen und *Zum Home-Bildschirm* nutzen (iPhone: Teilen-Button; Android: Drei-Punkte-Menü).\n\n💡 Du bekommst ein Icon wie bei jeder App, Start im Vollbild.'
 },
 historial:{
  es:'📈 **Historial** — Todo lo acumulado: tu evolución y la del equipo a lo largo de la temporada.\n\nPodés comparar períodos y ver si un fundamento mejoró o se cayó. Se puede filtrar por partido o por entrenamiento.\n\n💡 Es donde mejor se ve si el trabajo de las últimas semanas dio resultado.',
  en:'📈 **History** — Everything accumulated: your progression and the team\'s across the season.\n\nCompare periods and see whether a skill improved or dropped. Filter by match or training.\n\n💡 The best place to see whether recent work paid off.',
  de:'📈 **Verlauf** — Alles Kumulierte: deine Entwicklung und die des Teams über die Saison.\n\nZeiträume vergleichen und sehen, ob ein Element besser oder schlechter wurde. Filter nach Spiel oder Training.\n\n💡 Hier sieht man am besten, ob die Arbeit der letzten Wochen gewirkt hat.'
 },

 help:{
  es:'Te puedo ayudar con:\n• 📊 Stats de un jugador — escribí su apellido (ej. "¿cómo viene Durdos?")\n• 🏐 Mejores del equipo — "mejor sacador", "quién ataca mejor", "mejor receptor"\n• 📅 Próximo rival\n• 🏆 Tabla de la liga\n• ❓ Cómo usar: wellness, rutinas, pizarrón, scouting, game plan, video, PIN de acceso, qué es el EFF.',
  en:'I can help with:\n• 📊 A player\'s stats — type their surname (e.g. "how is Durdos doing?")\n• 🏐 Team leaders — "best server", "who attacks best", "best receiver"\n• 📅 Next rival\n• 🏆 League table\n• ❓ How to use: wellness, routines, board, scouting, game plan, video, access PIN, what EFF means.',
  de:'Ich helfe bei:\n• 📊 Stats eines Spielers — Nachname eingeben (z.B. "wie spielt Durdos?")\n• 🏐 Team-Beste — "bester Aufschläger", "wer greift am besten an", "beste Annahme"\n• 📅 Nächster Gegner\n• 🏆 Liga-Tabelle\n• ❓ Bedienung: Wellness, Trainingspläne, Tafel, Scouting, Game Plan, Video, Zugang-PIN, was EFF bedeutet.'
 },
 rutina:{
  es:'Armar una rutina (Preparador Físico):\n1. Entrá con PIN 0000.\n2. Elegí Jugador + Mes y tocá "Cargar".\n3. "+ Agregar día/sesión" → "+ Bloque" → "+ Ejercicio" (series/reps/descanso/nota).\n4. 💾 GUARDAR RUTINA. El jugador la ve al instante en Prep Física y en el Pizarrón.',
  en:'Build a routine (Physical Trainer):\n1. Log in with PIN 0000.\n2. Pick Player + Month and tap "Load".\n3. "+ Add day/session" → "+ Block" → "+ Exercise" (series/reps/rest/note).\n4. 💾 SAVE ROUTINE. The player sees it instantly in Prep Física and the Board.',
  de:'Trainingsplan erstellen (Athletiktrainer):\n1. Mit PIN 0000 einloggen.\n2. Spieler + Monat wählen, "Laden" tippen.\n3. "+ Tag/Einheit" → "+ Block" → "+ Übung" (Sätze/Wdh./Pause/Notiz).\n4. 💾 PLAN SPEICHERN. Der Spieler sieht ihn sofort in Prep Física und auf der Tafel.'
 },
 wellness:{
  es:'Wellness (lo carga cada jugador):\n1. Entrá con tu PIN (tu número de camiseta en 4 dígitos, ej. #17 → 0017).\n2. Abrí Wellness y respondé la encuesta diaria del 1 al 10 (sueño, energía, piernas, cuerpo, ánimo, estrés) + el RPE de la sesión.\n3. Se guarda solo en la nube. El cuerpo técnico ve la tabla del equipo y el % de readiness.',
  en:'Wellness (each player fills it):\n1. Log in with your PIN (jersey number as 4 digits, e.g. #17 → 0017).\n2. Open Wellness and answer the daily 1–10 survey (sleep, energy, legs, body, mood, stress) + session RPE.\n3. It auto-saves to the cloud. Staff sees the team table and each readiness %.',
  de:'Wellness (jeder Spieler):\n1. Mit deinem PIN einloggen (Trikotnummer 4-stellig, z.B. #17 → 0017).\n2. Wellness öffnen und die tägliche 1–10 Umfrage ausfüllen (Schlaf, Energie, Beine, Körper, Stimmung, Stress) + Session-RPE.\n3. Speichert automatisch in der Cloud. Das Trainerteam sieht die Tabelle und das Readiness-%.'
 },
 pizarron:{
  es:'Pizarrón:\n1. Elegí Mes + Día y qué jugadores mostrar.\n2. Todos ven la rutina del día y pueden anotar los pesos ahí (se sincroniza con Prep Física).\nIdeal para mostrar en la tablet o TV del gimnasio.',
  en:'Board (Pizarrón):\n1. Pick Month + Day and which players to show.\n2. Everyone sees the day\'s routine and can log weights there (syncs with Prep Física).\nGreat for the gym tablet/TV.',
  de:'Tafel (Pizarrón):\n1. Monat + Tag wählen und welche Spieler angezeigt werden.\n2. Alle sehen den Tagesplan und können dort Gewichte eintragen (synchron mit Prep Física).\nIdeal für Tablet/TV im Kraftraum.'
 },
 scouting:{
  es:'Scouting Rival: dossier completo de cada rival — saque, direcciones de ataque por rematador, distribución del armador por llamada y POR ROTACIÓN (side-out con recepción positiva vs transición), recepción y forma reciente. Hub → Scouting.',
  en:'Rival Scouting: full dossier per rival — serve, attack directions per hitter, setter distribution by call and BY ROTATION (side-out with positive reception vs transition), reception and recent form. Hub → Scouting.',
  de:'Gegner-Scouting: komplettes Dossier pro Gegner — Aufschlag, Angriffsrichtungen pro Angreifer, Zuspieler-Verteilung nach Zuspiel und NACH ROTATION (Side-out mit positiver Annahme vs Transition), Annahme und aktuelle Form. Hub → Scouting.'
 },
 gameplan:{
  es:'Game Plan: cómo jugarle a un rival — cómo atacan, dónde y cómo sacarles, y sus rotaciones débiles. Se abre desde Scouting o con game_plan.html?rival=NOMBRE. Sale de los datos de la liga.',
  en:'Game Plan: how to play a rival — how they attack, where/how to serve them, and their weak rotations. Open it from Scouting or game_plan.html?rival=NAME. Built from league data.',
  de:'Game Plan: wie man gegen einen Gegner spielt — wie sie angreifen, wohin/wie aufschlagen, und ihre schwachen Rotationen. Über Scouting oder game_plan.html?rival=NAME. Aus den Liga-Daten.'
 },
 video:{
  es:'Video / Cortes: ver y organizar cortes de video del equipo y de rivales. Entrá desde el Hub (Cortes / Video). Los videos se cargan desde un Excel y se publican junto con el resto.',
  en:'Video / Clips: view and organize video clips of the team and rivals. Open from the Hub (Cortes / Video). Clips are loaded from an Excel and published with the rest.',
  de:'Video / Clips: Videoclips vom Team und Gegnern ansehen und ordnen. Über das Hub (Cortes / Video). Clips werden aus einer Excel geladen und mitveröffentlicht.'
 },
 acceso:{
  es:'Acceso (PIN en la página de inicio):\n• Jugador: elegí tu nombre, PIN = tu número de camiseta en 4 dígitos (#17 → 0017).\n• Entrenador/Staff: 1009.\n• Preparador Físico: 0000 (abre Armar Rutinas).\n• Asistente Técnico: 9999 (acceso completo para cargar datos).',
  en:'Access (PIN on the home page):\n• Player: pick your name, PIN = jersey number as 4 digits (#17 → 0017).\n• Coach/Staff: 1009.\n• Physical Trainer: 0000 (opens Build Routines).\n• Technical Assistant: 9999 (full access to load data).',
  de:'Zugang (PIN auf der Startseite):\n• Spieler: Namen wählen, PIN = Trikotnummer 4-stellig (#17 → 0017).\n• Trainer/Staff: 1009.\n• Athletiktrainer: 0000 (öffnet Trainingspläne).\n• Co-Trainer: 9999 (Vollzugriff zum Daten laden).'
 },
 prepfisica:{
  es:'Prep Física (cada jugador): ves tu rutina del mes, anotás el peso de cada serie (se guarda solo), usás la calculadora de 1RM y ves tu readiness del wellness arriba. La rutina la arma el Preparador Físico.',
  en:'Prep Física (each player): see your monthly routine, log the weight of every set (auto-saved), use the 1RM calculator, and see your wellness readiness on top. The Physical Trainer builds the routine.',
  de:'Prep Física (jeder Spieler): deinen Monatsplan sehen, Gewicht jedes Satzes eintragen (speichert automatisch), 1RM-Rechner nutzen und oben dein Wellness-Readiness sehen. Den Plan erstellt der Athletiktrainer.'
 },
 eff:{
  es:'Conceptos de stats:\n• EFF de Ataque = (kills − errores − bloqueados) / total × 100. 🟢 ≥44%, 🟡 ≥36%, 🔴 <36%.\n• SO = Side Out (con recepción), TR = Transición.\n• Llamadas: K1 corta adelante, K7 seven, KM corrida, K2 corta atrás.\n• Dirección de ataque: solo cuentan las zonas profundas (1,5,6,7,8,9); los toques de bloque cortos se filtran.\n• Readiness = promedio de los 6 ítems del wellness × 10.',
  en:'Stats concepts:\n• Attack EFF = (kills − errors − blocked) / total × 100. 🟢 ≥44%, 🟡 ≥36%, 🔴 <36%.\n• SO = Side Out (off reception), TR = Transition.\n• Calls: K1 front quick, K7 seven, KM shifted, K2 back quick.\n• Attack direction: only deep zones count (1,5,6,7,8,9); short block touches are filtered out.\n• Readiness = average of the 6 wellness items × 10.',
  de:'Stat-Begriffe:\n• Angriff-EFF = (Punkte − Fehler − geblockt) / total × 100. 🟢 ≥44%, 🟡 ≥36%, 🔴 <36%.\n• SO = Side Out (nach Annahme), TR = Transition.\n• Zuspiele: K1 kurz vorne, K7 Seven, KM verschoben, K2 kurz hinten.\n• Angriffsrichtung: nur tiefe Zonen zählen (1,5,6,7,8,9); kurze Blockberührungen werden gefiltert.\n• Readiness = Durchschnitt der 6 Wellness-Werte × 10.'
 },
 fallback:{
  es:'No estoy seguro de eso 🤔. Puedo darte: stats de un jugador (escribí su apellido), los mejores del equipo (sacador/atacante/receptor), el próximo rival, la tabla de la liga, o cómo usar wellness / rutinas / pizarrón / scouting / game plan. Probá una sugerencia 👇',
  en:'Not sure about that 🤔. I can give you: a player\'s stats (type a surname), team leaders (server/attacker/receiver), the next rival, the league table, or how to use wellness / routines / board / scouting / game plan. Try a suggestion 👇',
  de:'Da bin ich nicht sicher 🤔. Ich kann: Stats eines Spielers (Nachname), Team-Beste (Aufschlag/Angriff/Annahme), nächster Gegner, Liga-Tabelle, oder Bedienung von Wellness / Plänen / Tafel / Scouting / Game Plan. Probier einen Vorschlag 👇'
 }
};

function vbFindPlayer(t){
  if(!DATA.players)return null;
  var toks=t.split(/[^a-z0-9]+/).filter(function(x){return x.length>=4;});
  if(!toks.length)return null;
  var cands=[];
  for(var i=0;i<DATA.players.length;i++){
    var p=DATA.players[i]; var words=vbNorm(p.name).split(/\s+/); var hit=false;
    for(var w=0;w<words.length&&!hit;w++){ var nw=words[w]; if(nw.length<4)continue;
      for(var x=0;x<toks.length;x++){ var tk=toks[x]; if(nw.indexOf(tk)===0||tk.indexOf(nw)===0){hit=true;break;} } }
    if(hit)cands.push(p);
  }
  if(!cands.length)return null;
  var naf=cands.filter(function(p){return p.team==='Nafels';});
  return (naf.length?naf:cands)[0];
}

function vbPlayerAnswer(p,lang){
  var L={es:{atk:'Ataque',srv:'Saque',rec:'Recepción',blk:'Bloqueo',ace:'aces',acc:'acc.',see:'Mirá el detalle en su ficha (Jugador) o en el Dashboard.'},
         en:{atk:'Attack',srv:'Serve',rec:'Reception',blk:'Block',ace:'aces',acc:'act.',see:'See the detail in their player card or the Dashboard.'},
         de:{atk:'Angriff',srv:'Aufschlag',rec:'Annahme',blk:'Block',ace:'Asse',acc:'Akt.',see:'Details in der Spielerkarte oder im Dashboard.'}}[lang];
  var lines=['📊 '+p.name+' (#'+p.num+(p.pos_label?', '+p.pos_label:'')+')'+(p.team!=='Nafels'?' — '+p.team:'')+':'];
  if(p.atk_tot>0){var c=p.atk_eff>=44?'🟢':(p.atk_eff>=36?'🟡':'🔴');lines.push('• '+L.atk+': '+vbFmt(p.atk_eff)+'% EFF '+c+' ('+p.atk_tot+')');}
  if(p.srv_tot>0){lines.push('• '+L.srv+': '+vbFmt(p.srv_eff)+'% EFF ('+p.srv_tot+', '+vbFmt(p.srv_ace)+'% '+L.ace+')');}
  if(p.rec_tot>0){lines.push('• '+L.rec+': '+vbFmt(p.rec_eff)+'% ('+p.rec_tot+')');}
  if(p.blk_tot>0){lines.push('• '+L.blk+': '+vbFmt(p.blk_eff)+'% ('+p.blk_tot+' '+L.acc+')');}
  lines.push(L.see);
  return lines.join('\n');
}

function vbRanking(t,lang){
  if(!DATA.players)return KB.fallback[lang];
  var liga=/liga|league/.test(t);
  var pool=DATA.players.filter(function(p){return liga?true:p.team==='Nafels';});
  var skill='atk',key='atk_eff',totk='atk_tot',min=50;
  if(/saque|serve|aufschlag|sacador|aufschlager/.test(t)){skill='srv';key='srv_eff';totk='srv_tot';}
  else if(/recep|reception|annahme|receptor/.test(t)){skill='rec';key='rec_eff';totk='rec_tot';}
  else if(/bloq|block/.test(t)){skill='blk';key='blk_eff';totk='blk_tot';min=20;}
  var arr=pool.filter(function(p){return p[totk]>=min && p[key]!=null;}).sort(function(a,b){return b[key]-a[key];}).slice(0,3);
  if(!arr.length)return KB.fallback[lang];
  var head={es:{atk:'Mejores en ataque',srv:'Mejores al saque',rec:'Mejores en recepción',blk:'Mejores en bloqueo'},
            en:{atk:'Best attackers',srv:'Best servers',rec:'Best receivers',blk:'Best blockers'},
            de:{atk:'Beste Angreifer',srv:'Beste Aufschläger',rec:'Beste Annahme',blk:'Beste Blocker'}}[lang][skill];
  var scope=liga?(lang==='es'?' (toda la liga)':lang==='de'?' (ganze Liga)':' (whole league)'):' (Näfels)';
  var out=['🏐 '+head+scope+':'];
  for(var i=0;i<arr.length;i++){var p=arr[i];out.push((i+1)+'. '+p.name+(p.team!=='Nafels'?' ('+p.team+')':'')+' — '+vbFmt(p[key])+'% ('+p[totk]+')');}
  return out.join('\n');
}

function vbNextRival(lang){
  var f=DATA.fixture&&DATA.fixture.proximo;
  if(!f)return {es:'No tengo el próximo rival cargado todavía.',en:'No next rival loaded yet.',de:'Noch kein nächster Gegner geladen.'}[lang];
  var c=f.cond||'';
  return {es:'📅 Próximo partido: vs '+f.rival+' ('+c+'), el '+f.fecha+'.\nPara prepararlo, entrá a Scouting Rival y al Game Plan de '+f.rival+'.',
          en:'📅 Next match: vs '+f.rival+' ('+c+'), on '+f.fecha+'.\nTo prepare, open Rival Scouting and the Game Plan for '+f.rival+'.',
          de:'📅 Nächstes Spiel: vs '+f.rival+' ('+c+'), am '+f.fecha+'.\nVorbereitung: Gegner-Scouting und Game Plan für '+f.rival+' öffnen.'}[lang];
}

function vbLeague(lang){
  var top=null;
  if(DATA.teams&&DATA.teams.length){top=DATA.teams.slice().filter(function(x){return x.atk_eff!=null;}).sort(function(a,b){return b.atk_eff-a.atk_eff;})[0];}
  var base={es:'🏆 La tabla completa está en "Estadísticas Liga" (botón del Hub): ranking por equipo y stats de todos los jugadores.',
            en:'🏆 The full table is in "Estadísticas Liga" (Hub button): team ranking and all players\' stats.',
            de:'🏆 Die komplette Tabelle ist unter "Estadísticas Liga" (Hub-Button): Team-Ranking und Stats aller Spieler.'}[lang];
  if(top){base+={es:'\nMejor EFF de ataque ahora: '+top.team+' ('+vbFmt(top.atk_eff)+'%).',
                 en:'\nBest attack EFF right now: '+top.team+' ('+vbFmt(top.atk_eff)+'%).',
                 de:'\nBeste Angriff-EFF aktuell: '+top.team+' ('+vbFmt(top.atk_eff)+'%).'}[lang];}
  return base;
}

function vbAnswer(raw){
  var lang=vbLang(raw); var t=vbNorm(raw);
  if(/\b(hola|buenas|hi|hello|hey|hallo|ayuda|help|hilfe|menu)\b/.test(t)||/que podes|que puedes|what can you|was kannst/.test(t))return KB.help[lang];
  if(/proximo|next|naechst|nachst|rival|gegner|contra quien|cuando jugamos|when do we play|wann spielen/.test(t))return vbNextRival(lang);
  if(/mejor|best|beste|top|quien ataca|quien saca|quien recibe|who attacks|who serves|goleador|ranking|wer greift|wer schlagt/.test(t))return vbRanking(t,lang);
  if(/playbook|play ?book|libro de juego|spielbuch/.test(t))return KB.playbook[lang];
  if(/calendario|fixture|partidos|calendar|kalender|cuando jugamos|when do we play|wann spielen/.test(t))return KB.calendario[lang];
  if(/corte|clip|mis jugadas|my clips|video ?clips/.test(t))return KB.cortes[lang];
  if(/heat ?map|mapa de calor|zonas|waermebild|warmebild/.test(t))return KB.heatmap[lang];
  if(/bateria|baterias|battery|batterie/.test(t))return KB.baterias[lang];
  if(/mi rendimiento|mis stats|mis numeros|my stats|my performance|meine stats|meine leistung/.test(t))return KB.miperfil[lang];
  if(/aviso|notificacion|notification|push|benachrichtigung|alerta/.test(t))return KB.avisos[lang];
  if(/me pide.*clave|volvio a pedir|sesion|session|anmeldung|cerraron/.test(t))return KB.sesion[lang];
  if(/idioma|language|sprache|ingles|aleman|english|deutsch/.test(t))return KB.idioma[lang];
  if(/celular|movil|telefono|phone|handy|instalar|install|app en el/.test(t))return KB.celular[lang];
  if(/historial|evolucion|progreso|history|progress|verlauf|entwicklung/.test(t))return KB.historial[lang];
  if(/rutina|routine|trainingsplan/.test(t))return KB.rutina[lang];
  if(/wellness|bienestar|befinden/.test(t))return KB.wellness[lang];
  if(/pizarr|board|tafel/.test(t))return KB.pizarron[lang];
  if(/scouting|scout|dossier/.test(t))return KB.scouting[lang];
  if(/game ?plan|plan de partido|plan del partido|spielplan/.test(t))return KB.gameplan[lang];
  if(/video|corte|clip/.test(t))return KB.video[lang];
  if(/\bpin\b|acceso|login|entrar|contrasena|password|passwort|zugang/.test(t))return KB.acceso[lang];
  if(/prep fisica|preparacion fisica|gimnasio|pesas|\bgym\b|1rm|kraftraum/.test(t))return KB.prepfisica[lang];
  if(/\beff\b|eficiencia|efficiency|effizienz|side ?out|\bso\b|\btr\b|transicion|transition|\bzona/.test(t))return KB.eff[lang];
  var p=vbFindPlayer(t); if(p)return vbPlayerAnswer(p,lang);
  if(/tabla|liga|league|tabelle|equipo|team|mannschaft|standing|clasificacion/.test(t))return vbLeague(lang);
  return KB.fallback[lang];
}

function vbCall(msg){
  vbLoading=true; var sb=document.getElementById('vb-send'); if(sb)sb.disabled=true;
  vbHistory.push({role:'user',content:msg});
  var tid=vbTyping();
  vbLoadData().then(function(){
    var reply; try{reply=vbAnswer(msg);}catch(e){reply=KB.fallback[vbLang(msg)]||KB.fallback.es;}
    vbHistory.push({role:'bot',content:reply});
    setTimeout(function(){
      vbRmTyping(tid); vbAdd('bot',reply); vbSuggs(msg);
      vbLoading=false; if(sb)sb.disabled=false;
    },300);
  });
}

function vbAdd(role,text){
  var msgs=document.getElementById('vb-chat-msgs');
  var d=document.createElement('div'); d.className='vb-msg vb-'+role;
  var av=document.createElement('div'); av.className='vb-avatar'; av.textContent=role==='bot'?'\ud83c\udfc0':'\ud83d\udc64';
  var b=document.createElement('div'); b.className='vb-bubble';
  b.innerHTML=text.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
    .replace(/\*\*([^*]+)\*\*/g,'<strong>$1</strong>').replace(/\n/g,'<br>');
  d.appendChild(av); d.appendChild(b); msgs.appendChild(d);
  msgs.scrollTop=msgs.scrollHeight;
  if(!vbOpen&&role==='bot'){var dot=document.getElementById('vb-chat-dot');if(dot){dot.style.display='block';setTimeout(function(){dot.style.display='none';},4000);}}
}

function vbTyping(){
  var msgs=document.getElementById('vb-chat-msgs');
  var id='vbt-'+Date.now();
  var d=document.createElement('div'); d.className='vb-msg vb-bot'; d.id=id;
  d.innerHTML='<div class="vb-avatar">\ud83c\udfc0</div><div class="vb-bubble vb-typing"><span></span><span></span><span></span></div>';
  msgs.appendChild(d); msgs.scrollTop=msgs.scrollHeight; return id;
}

function vbRmTyping(id){var el=document.getElementById(id);if(el)el.remove();}

function vbSuggs(q){
  var el=document.getElementById('vb-suggestions'); if(!el)return;
  var l=vbLang(q); LANG=l;
  var sets=SUGG[l]||SUGG.es;
  var set=sets[Math.floor(Math.random()*sets.length)];
  el.innerHTML=set.map(function(s){return '<button class="vb-sugg" onclick="vbSugg(this)">'+s+'</button>';}).join('');
  el.style.display='flex';
}

function vbResize(el){el.style.height='40px';el.style.height=Math.min(el.scrollHeight,110)+'px';}

setTimeout(function(){if(!vbOpen){var d=document.getElementById('vb-chat-dot');if(d){d.style.display='block';setTimeout(function(){d.style.display='none';},3500);}}},2000);

document.addEventListener('click',function(e){
  var p=document.getElementById('vb-chat-panel');
  var b=document.getElementById('vb-chat-btn');
  if(vbOpen&&p&&!p.contains(e.target)&&b&&!b.contains(e.target)){vbOpen=false;p.classList.remove('vb-open');}
});

// Expose to global scope for onclick handlers
window.vbToggle = vbToggle;
window.vbSend   = vbSend;
window.vbSugg   = vbSugg;
window.vbResize = vbResize;

})();

/* © 2025-2026 Ignacio Verdi · NAFELS VOLEY · Software propietario - Todos los derechos reservados */
