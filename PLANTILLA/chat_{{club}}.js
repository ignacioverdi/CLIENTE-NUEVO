(function(){

// ── CHAT IA VOLLEY {{CLUB}} — Self-contained widget ──────────────────
var CSS = [
  '#vb-chat-btn{position:fixed;bottom:24px;right:24px;width:58px;height:58px;border-radius:50%;border:none;cursor:pointer;z-index:9000;background:transparent;padding:0;filter:drop-shadow(0 4px 18px rgba(37,99,235,.55));transition:transform .2s,filter .2s}',
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
  '<svg viewBox="0 0 58 58" xmlns="http://www.w3.org/2000/svg">',
  '<circle cx="29" cy="29" r="28" fill="#1e3a8a"/>',
  '<circle cx="29" cy="29" r="27" fill="#dbeafe"/>',
  '<path d="M2,12 Q6,4 14,2 Q17,9 12,16 Q7,13 2,12Z" fill="#1e3a8a" opacity=".9"/>',
  '<path d="M25,2 Q33,5 37,12 Q31,16 25,12 Q25,7 25,2Z" fill="#1e3a8a" opacity=".9"/>',
  '<path d="M8,32 Q13,38 22,38 Q23,32 18,27 Q13,29 8,32Z" fill="#1e3a8a" opacity=".9"/>',
  '<g fill="none" stroke="#fbbf24" stroke-width="2.2" stroke-linecap="round">',
  '<path d="M14,2 Q22,10 24,9 Q28,6 25,2"/><path d="M25,2 Q24,12 28,17 Q32,16 37,12"/>',
  '<path d="M8,32 Q12,25 12,18 Q7,15 2,20"/><path d="M2,12 Q7,15 12,16 Q15,10 14,2"/>',
  '</g><ellipse cx="21" cy="17" rx="6" ry="4" fill="white" opacity=".25" transform="rotate(-20,21,17)"/>',
  '</svg></button>',
  '<div id="vb-chat-panel">',
  '<div class="vb-hdr">',
  '<svg class="vb-hdr-ball" viewBox="0 0 30 30" xmlns="http://www.w3.org/2000/svg"><circle cx="15" cy="15" r="14" fill="#1e3a8a"/><circle cx="15" cy="15" r="13" fill="#dbeafe"/><path d="M2,8 Q5,3 10,2 Q12,6 8,11 Q5,9 2,8Z" fill="#1e3a8a" opacity=".9"/><path d="M16,2 Q21,4 24,8 Q20,11 16,8 Q16,5 16,2Z" fill="#1e3a8a" opacity=".9"/><path d="M5,20 Q8,24 14,24 Q15,20 12,17 Q9,18 5,20Z" fill="#1e3a8a" opacity=".9"/><g fill="none" stroke="#fbbf24" stroke-width="1.5" stroke-linecap="round"><path d="M10,2 Q14,7 15,6 Q18,4 16,2"/><path d="M16,2 Q15,8 18,11 Q21,10 24,8"/></g></svg>',
  '<div class="vb-hdr-info"><div class="vb-hdr-title">ASISTENTE {{CLUB}}</div><div class="vb-hdr-sub"><div class="vb-dot-g"></div><span>IA aktiv</span></div></div>',
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
 help:{
  es:'Te puedo ayudar con:\n• 📊 Stats de un jugador — escribí su apellido (ej. "¿cómo viene JUGADOR?")\n• 🏐 Mejores del equipo — "mejor sacador", "quién ataca mejor", "mejor receptor"\n• 📅 Próximo rival\n• 🏆 Tabla de la liga\n• ❓ Cómo usar: wellness, rutinas, pizarrón, scouting, game plan, video, PIN de acceso, qué es el EFF.',
  en:'I can help with:\n• 📊 A player\'s stats — type their surname (e.g. "how is JUGADOR doing?")\n• 🏐 Team leaders — "best server", "who attacks best", "best receiver"\n• 📅 Next rival\n• 🏆 League table\n• ❓ How to use: wellness, routines, board, scouting, game plan, video, access PIN, what EFF means.',
  de:'Ich helfe bei:\n• 📊 Stats eines Spielers — Nachname eingeben (z.B. "wie spielt JUGADOR?")\n• 🏐 Team-Beste — "bester Aufschläger", "wer greift am besten an", "beste Annahme"\n• 📅 Nächster Gegner\n• 🏆 Liga-Tabelle\n• ❓ Bedienung: Wellness, Trainingspläne, Tafel, Scouting, Game Plan, Video, Zugang-PIN, was EFF bedeutet.'
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
  var naf=cands.filter(function(p){return p.team==='{{Club}}';});
  return (naf.length?naf:cands)[0];
}

function vbPlayerAnswer(p,lang){
  var L={es:{atk:'Ataque',srv:'Saque',rec:'Recepción',blk:'Bloqueo',ace:'aces',acc:'acc.',see:'Mirá el detalle en su ficha (Jugador) o en el Dashboard.'},
         en:{atk:'Attack',srv:'Serve',rec:'Reception',blk:'Block',ace:'aces',acc:'act.',see:'See the detail in their player card or the Dashboard.'},
         de:{atk:'Angriff',srv:'Aufschlag',rec:'Annahme',blk:'Block',ace:'Asse',acc:'Akt.',see:'Details in der Spielerkarte oder im Dashboard.'}}[lang];
  var lines=['📊 '+p.name+' (#'+p.num+(p.pos_label?', '+p.pos_label:'')+')'+(p.team!=='{{Club}}'?' — '+p.team:'')+':'];
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
  var pool=DATA.players.filter(function(p){return liga?true:p.team==='{{Club}}';});
  var skill='atk',key='atk_eff',totk='atk_tot',min=50;
  if(/saque|serve|aufschlag|sacador|aufschlager/.test(t)){skill='srv';key='srv_eff';totk='srv_tot';}
  else if(/recep|reception|annahme|receptor/.test(t)){skill='rec';key='rec_eff';totk='rec_tot';}
  else if(/bloq|block/.test(t)){skill='blk';key='blk_eff';totk='blk_tot';min=20;}
  var arr=pool.filter(function(p){return p[totk]>=min && p[key]!=null;}).sort(function(a,b){return b[key]-a[key];}).slice(0,3);
  if(!arr.length)return KB.fallback[lang];
  var head={es:{atk:'Mejores en ataque',srv:'Mejores al saque',rec:'Mejores en recepción',blk:'Mejores en bloqueo'},
            en:{atk:'Best attackers',srv:'Best servers',rec:'Best receivers',blk:'Best blockers'},
            de:{atk:'Beste Angreifer',srv:'Beste Aufschläger',rec:'Beste Annahme',blk:'Beste Blocker'}}[lang][skill];
  var scope=liga?(lang==='es'?' (toda la liga)':lang==='de'?' (ganze Liga)':' (whole league)'):' ({{Club}})';
  var out=['🏐 '+head+scope+':'];
  for(var i=0;i<arr.length;i++){var p=arr[i];out.push((i+1)+'. '+p.name+(p.team!=='{{Club}}'?' ('+p.team+')':'')+' — '+vbFmt(p[key])+'% ('+p[totk]+')');}
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

/* © 2025-2026 Ignacio Verdi · {{CLUB_COMPLETO}} · Software propietario - Todos los derechos reservados */
