/* ════════════════════════════════════════════════════════════════════════════
   api/calendario.js — EL CALENDARIO QUE SE ACTUALIZA SOLO
   ----------------------------------------------------------------------------
   Devuelve el fixture completo —partidos y entrenamientos— en formato .ics,
   leyendo SIEMPRE lo que hay en Firebase en ese momento.

   POR QUE HACE FALTA ESTO Y NO ALCANZA CON UN BOTON
   El boton "agregar al calendario" baja una COPIA: si despues cambia un
   horario, el evento que el jugador ya guardo se queda viejo. Una suscripcion
   es distinta: Google y Apple vuelven a leer esta direccion cada varias horas,
   asi que un cambio en la app les llega solo.

   POR QUE ES PUBLICO
   Google y Apple leen la direccion desde SUS servidores, sin sesion iniciada.
   No hay forma de pedirles usuario y clave. Por eso este archivo —y solo el
   nodo "calendario" de Firebase— tienen que ser de lectura publica.
   Es el fixture: los horarios de los partidos ya estan en la web de la liga.
   NINGUN otro dato del club se expone: ni estadisticas, ni videos, ni planteles.

   PARA QUE FUNCIONE HAY QUE ABRIR ESE NODO EN FIREBASE:
       "calendario": { ".read": true }
   El resto de la base sigue cerrado como esta.

   CADA CUANTO SE ACTUALIZA
   Lo decide el telefono, no nosotros: Google suele releer cada 8-24 h y Apple
   cada 15 min-1 h. Un cambio de horario de ultimo momento hay que avisarlo
   igual por la app, como siempre.
   ════════════════════════════════════════════════════════════════════════════ */

const FB = 'https://nafels-voley-default-rtdb.firebaseio.com';
const TZ = 'Europe/Zurich';
const CLUB = 'Näfels';

/* ── DONDE VIVE EL CALENDARIO ────────────────────────────────────────────────
   No todos los clubes lo guardan en el mismo lugar. El club original lo tiene
   en la raiz (calendario/partidos), pero las instalaciones nuevas usan una
   rama por club: clubes/<club>/calendario/partidos, que es lo que arma
   arreglar_firebase.py.

   Se prueban las dos, en ese orden. Asi el mismo archivo sirve para los dos
   casos y no hay que acordarse de tocarlo al dar de alta un cliente. */
const RAMA = 'nafels';
const CAMINOS = [`clubes/${RAMA}/calendario`, 'calendario'];

/* El .ics escapa con barra invertida las comas, los punto y coma y los saltos
   de linea. Sin esto, una direccion como "Lintharena, Näfels" parte el campo
   en dos y el evento llega roto. */
function esc(t) {
  return String(t == null ? '' : t)
    .replace(/\\/g, '\\\\')
    .replace(/;/g, '\\;')
    .replace(/,/g, '\\,')
    .replace(/\r?\n/g, '\\n');
}

function fechaHora(fecha, hora) {
  return String(fecha || '').replace(/-/g, '') + 'T' + String(hora || '00:00').replace(':', '') + '00';
}

function masHoras(hora, n) {
  const p = String(hora || '00:00').split(':');
  const h = Math.min(parseInt(p[0], 10) + n, 23);
  return ('0' + h).slice(-2) + ':' + (p[1] || '00');
}

/* El dia SIGUIENTE al ultimo: en un evento de dia completo, el .ics pide que
   el fin sea exclusivo. Sin esto, unas vacaciones del 20 al 25 se verian
   hasta el 24. */
function diaSiguiente(fecha) {
  const d = new Date(fecha + 'T00:00:00Z');
  d.setUTCDate(d.getUTCDate() + 1);
  return d.toISOString().slice(0, 10).replace(/-/g, '');
}

function sello() {
  return new Date().toISOString().replace(/[-:]/g, '').split('.')[0] + 'Z';
}

function partido(e) {
  const rival  = e.rival || 'Partido';
  const visita = String(e.condicion || '').indexOf('Visit') === 0;
  const titulo = visita ? `${rival} vs ${CLUB}` : `${CLUB} vs ${rival}`;
  const hora   = e.hora || '00:00';
  return [
    'BEGIN:VEVENT',
    `UID:nafels-p-${e.id || (e.fecha + rival).replace(/\W/g, '')}@volley-nafels`,
    `DTSTAMP:${sello()}`,
    `DTSTART;TZID=${TZ}:${fechaHora(e.fecha, hora)}`,
    `DTEND;TZID=${TZ}:${fechaHora(e.fecha, masHoras(hora, 2))}`,
    `SUMMARY:${esc(titulo)}`,
    `LOCATION:${esc(e.lugar || '')}`,
    `DESCRIPTION:${esc((visita ? 'Visitante' : 'Local') + (e.lugar ? ' - ' + e.lugar : ''))}`,
    'BEGIN:VALARM',
    'TRIGGER:-PT2H',
    'ACTION:DISPLAY',
    `DESCRIPTION:${esc(titulo)}`,
    'END:VALARM',
    'END:VEVENT'
  ].join('\r\n');
}

function entrenamiento(e) {
  const titulo = e.tipo || 'Entrenamiento';
  const cab = [
    'BEGIN:VEVENT',
    `UID:nafels-e-${e.id || (e.fecha + titulo).replace(/\W/g, '')}@volley-nafels`,
    `DTSTAMP:${sello()}`
  ];
  let cuerpo;
  if (e.fechaFin && e.fechaFin > e.fecha) {
    /* varios dias (vacaciones, torneos): evento de dia completo */
    cuerpo = [
      `DTSTART;VALUE=DATE:${e.fecha.replace(/-/g, '')}`,
      `DTEND;VALUE=DATE:${diaSiguiente(e.fechaFin)}`
    ];
  } else {
    const h1 = e.hora || '00:00';
    const h2 = e.horaFin || masHoras(h1, 2);
    cuerpo = [
      `DTSTART;TZID=${TZ}:${fechaHora(e.fecha, h1)}`,
      `DTEND;TZID=${TZ}:${fechaHora(e.fecha, h2)}`
    ];
  }
  return cab.concat(cuerpo).concat([
    `SUMMARY:${esc(titulo)}`,
    `LOCATION:${esc(e.lugar || '')}`,
    'END:VEVENT'
  ]).join('\r\n');
}

/* Ninguna linea del .ics puede pasar de 75 octetos: las que se pasan se
   parten y la siguiente arranca con un espacio. Los lectores estrictos
   —Outlook sobre todo— descartan el evento entero si no se respeta. */
function plegar(linea) {
  const b = Buffer.from(linea, 'utf8');
  if (b.length <= 74) return linea;
  const partes = [];
  let i = 0;
  while (i < b.length) {
    let corte = Math.min(i + (i === 0 ? 74 : 73), b.length);
    /* no cortar en el medio de un caracter de varios bytes */
    while (corte > i && corte < b.length && (b[corte] & 0xC0) === 0x80) corte--;
    partes.push((i === 0 ? '' : ' ') + b.slice(i, corte).toString('utf8'));
    i = corte;
  }
  return partes.join('\r\n');
}

export default async function handler(req, res) {
  let eventos = [];
  try {
    /* Se prueba rama por club y despues la raiz. El parametro suelto evita
       que Firebase devuelva una copia guardada. */
    let d = {};
    for (const camino of CAMINOS) {
      try {
        const r = await fetch(`${FB}/${camino}.json?ts=${Date.now()}`);
        const x = await r.json();
        if (x && (x.partidos || x.entrenamientos)) { d = x; break; }
      } catch (_) { /* se prueba el siguiente */ }
    }
    /* Firebase NO siempre devuelve una lista. Si los indices no son 0,1,2...
       —porque se borro un partido del medio, por ejemplo— la guarda como un
       objeto con claves numericas. Un Array.isArray() sobre eso da false y se
       perdian todos los eventos sin ningun aviso. */
    const aLista = (x) => Array.isArray(x) ? x : (x && typeof x === 'object' ? Object.values(x) : []);
    const partidos = aLista(d.partidos);
    const entrenos = aLista(d.entrenamientos);
    eventos = partidos.filter(e => e && e.fecha).map(partido)
      .concat(entrenos.filter(e => e && e.fecha).map(entrenamiento));
  } catch (e) {
    /* Si Firebase no contesta, se devuelve un calendario VACIO pero valido.
       Devolver un error haria que el telefono marque la suscripcion como rota
       y algunos la desactivan solas. Vacio se recupera en la proxima lectura. */
    eventos = [];
  }

  const ics = [
    'BEGIN:VCALENDAR',
    'VERSION:2.0',
    'PRODID:-//Volley Nafels//Calendario//ES',
    'CALSCALE:GREGORIAN',
    'METHOD:PUBLISH',
    `X-WR-CALNAME:${CLUB} Voley`,
    `X-WR-TIMEZONE:${TZ}`,
    'X-PUBLISHED-TTL:PT6H'      /* sugerencia al telefono: releer cada 6 h */
  ].concat(eventos).concat(['END:VCALENDAR'])
   .join('\r\n').split('\r\n').map(plegar).join('\r\n');

  res.setHeader('Content-Type', 'text/calendar; charset=utf-8');
  res.setHeader('Content-Disposition', 'inline; filename="nafels.ics"');
  /* Sin cache. Un calendario que se actualiza solo no puede quedar servido
     de una copia: si se corrige un horario, tiene que salir en la proxima
     lectura. Google y Apple releen cada varias horas igual, asi que no hay
     riesgo de sobrecarga. */
  res.setHeader('Cache-Control', 'no-store, max-age=0');
  res.status(200).send(ics);
}
