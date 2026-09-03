/* ═══════════════════════════════════════════════════════════════════════════
   ayuda.js — EL SIGNO DE PREGUNTA DE CADA PANTALLA

   Un boton "?" arriba a la derecha. Se toca y se abre una ventanita que
   explica, en dos minutos de lectura, que hace esa pantalla y como se usa.

   ── POR QUE ──────────────────────────────────────────────────────────────
   La app tiene 54 pantallas. Un entrenador que la abre por primera vez no
   tiene por que adivinar que hace cada una. Sin esto, la mitad de lo que
   hicimos no se usa nunca.

   ── COMO SE AGREGA A UNA PANTALLA ────────────────────────────────────────
   Una sola linea, al final del <body>:

       <script src="ayuda.js"></script>

   El resto es automatico: se fija en que pantalla esta, busca su texto y
   dibuja el boton. Si una pantalla todavia no tiene texto escrito, el boton
   no aparece —mejor nada que un cartel vacio—.

   ── LOS TRES IDIOMAS ─────────────────────────────────────────────────────
   Cada texto se escribe en es / en / de. Se usa el idioma que el usuario
   eligio con los botones ES EN DE, y cambia solo cuando lo cambia.

   ── COMO ESCRIBIR UNA AYUDA NUEVA ────────────────────────────────────────
   Se agrega al diccionario de abajo, con el nombre del archivo sin .html:

       'mi_pantalla': {
         es: { titulo:'...', que:'...', pasos:['...','...'], ojo:'...' },
         en: { ... }, de: { ... }
       }

   que    — una frase: para que sirve la pantalla
   pasos  — la lista de lo que hay que hacer, en orden
   ojo    — opcional: la advertencia que evita el error mas comun
   ═══════════════════════════════════════════════════════════════════════════ */

(function () {
  'use strict';

  /* ── Los textos ───────────────────────────────────────────────────────── */
  var AYUDA = {


    'dashboard': {
      es: {
        titulo: 'Dashboard',
        que: 'La puerta de entrada: desde acá se llega a todo el sistema.',
        pasos: [
          'Elegí el jugador y el fundamento que querés mirar.',
          'Tocá "Heat Maps" para ver los mapas de calor de cada fundamento.',
          'Cada tarjeta lleva a una pantalla distinta del sistema.'
        ]
      },
      en: {
        titulo: 'Dashboard',
        que: 'The way in: everything in the system is reachable from here.',
        pasos: [
          'Pick the player and the skill you want to look at.',
          'Tap "Heat Maps" to see the heat maps for each skill.',
          'Each card leads to a different screen of the system.'
        ]
      },
      de: {
        titulo: 'Dashboard',
        que: 'Der Einstieg: von hier aus ist alles im System erreichbar.',
        pasos: [
          'Wähle den Spieler und das Element, das du ansehen willst.',
          'Tippe auf "Heat Maps", um die Heatmaps jedes Elements zu sehen.',
          'Jede Kachel führt zu einem anderen Bildschirm des Systems.'
        ]
      }
    },

    'jugador': {
      es: {
        titulo: 'Perfil del Jugador',
        que: 'Todo lo de un jugador: sus números, su evolución y sus videos.',
        pasos: [
          'Arriba, el resumen de la temporada en cada fundamento.',
          'Abajo, sus once baterías comparadas con las del equipo.',
          'Verde llegó al objetivo, ámbar está cerca, rojo está lejos.',
          'Con "Stats" y "Rutina" pasás a su detalle y a su plan de trabajo.'
        ],
        ojo: 'Si el jugador entra con su cuenta, ve solo esta pantalla y lo suyo.'
      },
      en: {
        titulo: 'Player Profile',
        que: 'Everything about one player: their numbers, their progress and their videos.',
        pasos: [
          'At the top, the season summary for each skill.',
          'Below, their eleven target bars compared with the team\u2019s.',
          'Green reached the target, amber is close, red is far off.',
          'Use "Stats" and "Routine" for their detail and their work plan.'
        ],
        ojo: 'If the player logs in with their own account, they only see this screen and their own data.'
      },
      de: {
        titulo: 'Spielerprofil',
        que: 'Alles zu einem Spieler: seine Zahlen, seine Entwicklung und seine Videos.',
        pasos: [
          'Oben die Saisonübersicht für jedes Element.',
          'Darunter seine elf Zielbalken im Vergleich zum Team.',
          'Grün Ziel erreicht, Bernstein nah dran, Rot weit entfernt.',
          'Mit "Stats" und "Routine" geht es zu Details und Trainingsplan.'
        ],
        ojo: 'Meldet sich der Spieler selbst an, sieht er nur diesen Bildschirm und seine eigenen Daten.'
      }
    },

    'subir_partido': {
      es: {
        titulo: 'Subir un Partido',
        que: 'El archivo que scouteaste se procesa y actualiza toda la app.',
        pasos: [
          'Arrastrá el archivo .dvw del partido.',
          'Si el club tiene varias categorías, elegí a cuál pertenece.',
          'Pegá el link del video si lo tenés.',
          'Esperá a que termine: en minutos está todo actualizado.'
        ],
        ojo: 'Si la cámara cortó el partido en varios archivos, unilos antes con Unir Videos.'
      },
      en: {
        titulo: 'Upload a Match',
        que: 'The file you scouted gets processed and updates the whole app.',
        pasos: [
          'Drag in the match .dvw file.',
          'If the club has several categories, pick which one it belongs to.',
          'Paste the video link if you have one.',
          'Wait for it to finish: everything is updated within minutes.'
        ],
        ojo: 'If the camera split the match into several files, merge them first with Merge Videos.'
      },
      de: {
        titulo: 'Spiel hochladen',
        que: 'Die gescoutete Datei wird verarbeitet und aktualisiert die ganze App.',
        pasos: [
          'Ziehe die .dvw-Datei des Spiels hierher.',
          'Hat der Verein mehrere Kategorien, wähle die passende.',
          'Füge den Videolink ein, falls vorhanden.',
          'Warte bis es fertig ist: in Minuten ist alles aktualisiert.'
        ],
        ojo: 'Hat die Kamera das Spiel in mehrere Dateien geteilt, füge sie vorher mit Videos zusammenfügen zusammen.'
      }
    },

    'asociar_codigos': {
      es: {
        titulo: 'Asociar Códigos',
        que: 'Traduce el scouting de otra persona a tus propios códigos.',
        pasos: [
          'Arrastrá el archivo que te llegó.',
          'A la izquierda ves sus códigos, a la derecha los tuyos.',
          'Los idénticos se asocian solos; el resto los elegís vos.',
          'Guardá la asociación: la próxima vez que llegue un archivo de esa persona, la cargás y se aplica sola.'
        ],
        ojo: 'Sirve en las dos direcciones: también para traducir tus partidos antes de mandarlos afuera.'
      },
      en: {
        titulo: 'Match Codes',
        que: 'Translates someone else\u2019s scouting into your own codes.',
        pasos: [
          'Drag in the file you received.',
          'On the left you see their codes, on the right yours.',
          'Identical ones are matched automatically; you pick the rest.',
          'Save the mapping: next time a file arrives from that person, load it and it applies itself.'
        ],
        ojo: 'It works both ways: also to translate your matches before sending them out.'
      },
      de: {
        titulo: 'Codes zuordnen',
        que: 'Übersetzt das Scouting einer anderen Person in deine eigenen Codes.',
        pasos: [
          'Ziehe die erhaltene Datei hierher.',
          'Links siehst du ihre Codes, rechts deine.',
          'Identische werden automatisch zugeordnet; den Rest wählst du.',
          'Speichere die Zuordnung: beim nächsten Mal lädst du sie und sie wird automatisch angewendet.'
        ],
        ojo: 'Funktioniert in beide Richtungen: auch um deine Spiele vor dem Versand zu übersetzen.'
      }
    },

    'unir_video': {
      es: {
        titulo: 'Unir Videos',
        que: '¿La cámara cortó el partido en varios archivos? Acá se unen en uno.',
        pasos: [
          'Descargá el programa la primera vez. Después queda en tu computadora.',
          'Ponelo en la carpeta donde están las partes del partido.',
          'Doble click y esperá.',
          'Sale un solo archivo, listo para subir a YouTube o donde uses.'
        ],
        ojo: 'Si las partes son de la misma cámara se pegan sin recomprimir: tarda segundos y no pierde calidad.'
      },
      en: {
        titulo: 'Merge Videos',
        que: 'Did the camera split the match into several files? Here they become one.',
        pasos: [
          'Download the program the first time. After that it stays on your computer.',
          'Put it in the folder where the match parts are.',
          'Double-click and wait.',
          'You get a single file, ready to upload to YouTube or wherever you use.'
        ],
        ojo: 'If the parts come from the same camera they are joined without re-encoding: it takes seconds and loses no quality.'
      },
      de: {
        titulo: 'Videos zusammenfügen',
        que: 'Hat die Kamera das Spiel in mehrere Dateien geteilt? Hier werden sie zu einer.',
        pasos: [
          'Lade das Programm beim ersten Mal herunter. Danach bleibt es auf deinem Rechner.',
          'Lege es in den Ordner mit den Spielteilen.',
          'Doppelklick und warten.',
          'Es entsteht eine einzige Datei, bereit für YouTube oder wo auch immer.'
        ],
        ojo: 'Stammen die Teile von derselben Kamera, werden sie ohne Neukodierung verbunden: Sekunden, ohne Qualitätsverlust.'
      }
    },

    'wellness': {
      es: {
        titulo: 'Wellness',
        que: 'Cómo llega cada jugador al entrenamiento: sueño, ánimo y cansancio.',
        pasos: [
          'Cada jugador lo carga desde su celular, en treinta segundos.',
          'El cuerpo técnico ve la carga real del plantel, día a día.',
          'Sirve para ajustar el entrenamiento antes de que aparezca la lesión.'
        ],
        ojo: 'Conviene cargarlo ANTES de entrenar, no después: es para decidir la sesión, no para evaluarla.'
      },
      en: {
        titulo: 'Wellness',
        que: 'How each player arrives at training: sleep, mood and fatigue.',
        pasos: [
          'Each player fills it in from their phone, in thirty seconds.',
          'The staff sees the squad\u2019s real load, day by day.',
          'It helps adjust training before an injury shows up.'
        ],
        ojo: 'Fill it in BEFORE training, not after: it is meant to shape the session, not to review it.'
      },
      de: {
        titulo: 'Wellness',
        que: 'Wie jeder Spieler ins Training kommt: Schlaf, Stimmung und Müdigkeit.',
        pasos: [
          'Jeder Spieler füllt es in dreissig Sekunden am Handy aus.',
          'Das Trainerteam sieht die tatsächliche Belastung des Kaders, Tag für Tag.',
          'So lässt sich das Training anpassen, bevor eine Verletzung auftritt.'
        ],
        ojo: 'VOR dem Training ausfüllen, nicht danach: es soll die Einheit steuern, nicht bewerten.'
      }
    },

    'rotaciones': {
      es: {
        titulo: 'Rotaciones',
        que: 'Dónde se gana y dónde se pierde el partido, rotación por rotación.',
        pasos: [
          'Mirá el side-out de las seis rotaciones propias.',
          'Compará con el break point: ahí está la diferencia.',
          'Las rotaciones más bajas son las que hay que trabajar o esconder.'
        ],
        ojo: 'Una rotación con poco volumen puede mostrar un porcentaje engañoso. Fijate cuántas pelotas tiene.'
      },
      en: {
        titulo: 'Rotations',
        que: 'Where the match is won and lost, rotation by rotation.',
        pasos: [
          'Look at the side-out for your six rotations.',
          'Compare it with break point: that is where the difference is.',
          'The weakest rotations are the ones to work on or to hide.'
        ],
        ojo: 'A rotation with few rallies can show a misleading percentage. Check how many balls it has.'
      },
      de: {
        titulo: 'Rotationen',
        que: 'Wo das Spiel gewonnen und verloren wird, Rotation für Rotation.',
        pasos: [
          'Sieh dir den Side-out deiner sechs Rotationen an.',
          'Vergleiche mit dem Break Point: dort liegt der Unterschied.',
          'Die schwächsten Rotationen sind die, an denen zu arbeiten ist.'
        ],
        ojo: 'Eine Rotation mit wenigen Ballwechseln kann einen irreführenden Prozentsatz zeigen. Prüfe die Anzahl.'
      }
    },




    'hm_ataque': {
      es: { titulo:'Mapa de Ataque',
        que:'Adónde ataca cada jugador, sobre las nueve zonas del campo rival.',
        pasos:['Elegí el jugador arriba a la izquierda.','Filtrá por rival, por partido o por combinación.','Las zonas más calientes son donde más pelotas manda.'],
        ojo:'Doble click en una zona abre el video de esos ataques. Y "VER LOS VIDEOS" los abre todos.' },
      en: { titulo:'Attack Map',
        que:'Where each player attacks, across the nine zones of the opposing court.',
        pasos:['Pick the player at the top left.','Filter by opponent, match or combination.','The hottest zones are where they send most balls.'],
        ojo:'Double-click a zone to open the video of those attacks. "WATCH THE VIDEOS" opens them all.' },
      de: { titulo:'Angriffskarte',
        que:'Wohin jeder Spieler angreift, über die neun Zonen des gegnerischen Feldes.',
        pasos:['Wähle oben links den Spieler.','Filtere nach Gegner, Spiel oder Kombination.','Die heissesten Zonen sind, wohin die meisten Bälle gehen.'],
        ojo:'Doppelklick auf eine Zone öffnet das Video. "VIDEOS ANSEHEN" öffnet alle.' }
    },

    'hm_saque': {
      es: { titulo:'Mapa de Saque',
        que:'Adónde saca cada jugador y con qué resultado.',
        pasos:['Elegí el jugador.','Mirá a qué zonas apunta y dónde le sale mejor.','Filtrá por rival para preparar el próximo partido.'],
        ojo:'El saque se lee por punto directo, positivo y error. Un saque con muchos errores puede seguir siendo bueno si rompe la recepción.' },
      en: { titulo:'Serve Map',
        que:'Where each player serves and with what outcome.',
        pasos:['Pick the player.','See which zones they aim at and where it works best.','Filter by opponent to prepare the next match.'],
        ojo:'Serving is read by ace, positive and error. A serve with many errors can still be good if it breaks the reception.' },
      de: { titulo:'Aufschlagkarte',
        que:'Wohin jeder Spieler aufschlägt und mit welchem Ergebnis.',
        pasos:['Wähle den Spieler.','Sieh, welche Zonen er anvisiert und wo es am besten klappt.','Filtere nach Gegner für die Spielvorbereitung.'],
        ojo:'Der Aufschlag wird nach Ass, positiv und Fehler gelesen. Viele Fehler können trotzdem gut sein, wenn die Annahme bricht.' }
    },

    'hm_recepcion': {
      es: { titulo:'Mapa de Recepción',
        que:'Desde dónde le sacan a cada jugador y cómo responde.',
        pasos:['Elegí el jugador.','Las zonas muestran desde dónde le llegan los saques.','Compará la calidad según la zona de origen.'],
        ojo:'Lo que importa es la recepción positiva (#+): es la que deja armar todas las opciones.' },
      en: { titulo:'Reception Map',
        que:'Where each player gets served from and how they respond.',
        pasos:['Pick the player.','The zones show where the serves reach them from.','Compare the quality by origin zone.'],
        ojo:'What matters is positive reception (#+): that is the one that keeps every setting option open.' },
      de: { titulo:'Annahmekarte',
        que:'Woher jeder Spieler angeschlagen wird und wie er reagiert.',
        pasos:['Wähle den Spieler.','Die Zonen zeigen, woher die Aufschläge kommen.','Vergleiche die Qualität nach Ursprungszone.'],
        ojo:'Entscheidend ist die positive Annahme (#+): sie hält alle Zuspieloptionen offen.' }
    },

    'hm_armador': {
      es: { titulo:'Mapa del Armador',
        que:'A quién le pasa el armador en cada rotación y desde cada recepción.',
        pasos:['Elegí el armador.','Filtrá por rotación y por tipo de recepción.','Mirá el porcentaje de distribución y el de punto.'],
        ojo:'Sirve para los dos lados: para entender al armador rival y para revisar el propio.' },
      en: { titulo:'Setter Map',
        que:'Who the setter feeds in each rotation and from each reception.',
        pasos:['Pick the setter.','Filter by rotation and reception type.','Look at the distribution and point percentages.'],
        ojo:'Useful both ways: to read the opposing setter and to review your own.' },
      de: { titulo:'Zuspielkarte',
        que:'Wen der Zuspieler in jeder Rotation und aus jeder Annahme bedient.',
        pasos:['Wähle den Zuspieler.','Filtere nach Rotation und Annahmeart.','Achte auf Verteilungs- und Punktquote.'],
        ojo:'Nützlich in beide Richtungen: den gegnerischen Zuspieler lesen und den eigenen prüfen.' }
    },

    'ataque_jugador': {
      es: { titulo:'Ataque del Jugador',
        que:'Todo el ataque de un jugador: combinaciones, zonas y eficacia.',
        pasos:['Elegí el jugador.','Mirá qué combinación usa más y cuál le rinde mejor.'],
        ojo:'Una combinación con pocas pelotas puede mostrar un porcentaje engañoso. Fijate el volumen.' },
      en: { titulo:'Player Attack',
        que:'A player\u2019s full attack: combinations, zones and efficiency.',
        pasos:['Pick the player.','See which combination they use most and which pays off best.'],
        ojo:'A combination with few balls can show a misleading percentage. Check the volume.' },
      de: { titulo:'Angriff des Spielers',
        que:'Der gesamte Angriff eines Spielers: Kombinationen, Zonen und Effizienz.',
        pasos:['Wähle den Spieler.','Sieh, welche Kombination er am meisten nutzt und welche am besten läuft.'],
        ojo:'Eine Kombination mit wenigen Bällen kann irreführend sein. Prüfe das Volumen.' }
    },

    'saque_jugador': {
      es: { titulo:'Saque del Jugador',
        que:'El saque de un jugador en detalle: puntos, positivos y errores.',
        pasos:['Elegí el jugador.','Mirá el balance entre riesgo y resultado.'],
        ojo:'Cero errores suele significar que saca demasiado suave. El saque bueno tiene errores.' },
      en: { titulo:'Player Serve',
        que:'One player\u2019s serve in detail: aces, positives and errors.',
        pasos:['Pick the player.','Look at the balance between risk and outcome.'],
        ojo:'Zero errors usually means serving too softly. A good serve has errors.' },
      de: { titulo:'Aufschlag des Spielers',
        que:'Der Aufschlag eines Spielers im Detail: Asse, positive und Fehler.',
        pasos:['Wähle den Spieler.','Achte auf das Verhältnis von Risiko und Ergebnis.'],
        ojo:'Null Fehler heisst meist zu weich aufgeschlagen. Ein guter Aufschlag hat Fehler.' }
    },

    'recepcion_jugador': {
      es: { titulo:'Recepción del Jugador',
        que:'La recepción de un jugador en detalle, saque por saque.',
        pasos:['Elegí el jugador.','Mirá su porcentaje positivo y sus errores.'],
        ojo:'Compará contra los otros receptores del equipo, no contra un número absoluto.' },
      en: { titulo:'Player Reception',
        que:'One player\u2019s reception in detail, serve by serve.',
        pasos:['Pick the player.','Look at their positive percentage and their errors.'],
        ojo:'Compare against the team\u2019s other passers, not against an absolute number.' },
      de: { titulo:'Annahme des Spielers',
        que:'Die Annahme eines Spielers im Detail, Aufschlag für Aufschlag.',
        pasos:['Wähle den Spieler.','Sieh dir seine positive Quote und seine Fehler an.'],
        ojo:'Vergleiche mit den anderen Annahmespielern, nicht mit einem absoluten Wert.' }
    },

    'armadores': {
      es: { titulo:'Armadores',
        que:'La distribución de los armadores del equipo y de los rivales.',
        pasos:['Elegí el equipo y el armador.','Filtrá por fase y por tipo de recepción.','Mirá a quién le pasa en cada rotación.'],
        ojo:'Con recepción perfecta un armador usa todas las opciones; con recepción mala se le achica el juego. Compará las dos.' },
      en: { titulo:'Setters',
        que:'The distribution of your team\u2019s setters and the opponents\u2019.',
        pasos:['Pick the team and the setter.','Filter by phase and reception type.','See who they feed in each rotation.'],
        ojo:'With a perfect pass a setter uses every option; with a bad one the game shrinks. Compare both.' },
      de: { titulo:'Zuspieler',
        que:'Die Verteilung der eigenen und der gegnerischen Zuspieler.',
        pasos:['Wähle Team und Zuspieler.','Filtere nach Phase und Annahmeart.','Sieh, wen er in jeder Rotation bedient.'],
        ojo:'Bei perfekter Annahme nutzt ein Zuspieler alle Optionen, bei schlechter schrumpft das Spiel. Vergleiche beide.' }
    },

    'historial_voley': {
      es: { titulo:'Historial',
        que:'Todos los partidos jugados, con su resultado y sus números.',
        pasos:['Tocá un partido para ver su detalle.','Compará entre partidos para ver la evolución.'],
        ojo:'Cada categoría tiene su propio historial.' },
      en: { titulo:'History',
        que:'Every match played, with its result and its numbers.',
        pasos:['Tap a match to see its detail.','Compare between matches to see the progression.'],
        ojo:'Each category has its own history.' },
      de: { titulo:'Verlauf',
        que:'Alle gespielten Spiele mit Ergebnis und Zahlen.',
        pasos:['Tippe auf ein Spiel für die Details.','Vergleiche zwischen Spielen, um die Entwicklung zu sehen.'],
        ojo:'Jede Kategorie hat ihren eigenen Verlauf.' }
    },

    'importar_dvw': {
      es: { titulo:'Importar Scouting',
        que:'Cargar el archivo de un partido ya scouteado.',
        pasos:['Arrastrá el archivo .dvw.','Elegí la categoría si el club tiene varias.','Esperá a que termine de procesar.'],
        ojo:'Si el partido lo scouteó otra persona con sus propios códigos, pasalo antes por Asociar Códigos.' },
      en: { titulo:'Import Scouting',
        que:'Load the file of a match that was already scouted.',
        pasos:['Drag in the .dvw file.','Pick the category if the club has several.','Wait for it to finish processing.'],
        ojo:'If someone else scouted it with their own codes, run it through Match Codes first.' },
      de: { titulo:'Scouting importieren',
        que:'Die Datei eines bereits gescouteten Spiels laden.',
        pasos:['Ziehe die .dvw-Datei hierher.','Wähle die Kategorie, wenn der Verein mehrere hat.','Warte, bis die Verarbeitung fertig ist.'],
        ojo:'Hat jemand anderes mit eigenen Codes gescoutet, führe es vorher durch Codes zuordnen.' }
    },


    'manual': {
      es: { titulo:'Manual del Club',
        que:'Cómo se usa el sistema, explicado paso a paso.',
        pasos:['Buscá el tema que necesites en el índice.','Cada sección explica una parte de la app.'],
        ojo:'Para lo puntual de cada pantalla está este mismo botón "?" en cada una.' },
      en: { titulo:'Club Manual',
        que:'How the system is used, explained step by step.',
        pasos:['Find the topic you need in the index.','Each section covers one part of the app.'],
        ojo:'For screen-specific help, this same "?" button is on every screen.' },
      de: { titulo:'Vereinshandbuch',
        que:'Wie das System benutzt wird, Schritt für Schritt erklärt.',
        pasos:['Suche das gewünschte Thema im Inhaltsverzeichnis.','Jeder Abschnitt behandelt einen Teil der App.'],
        ojo:'Für bildschirmspezifische Hilfe gibt es diesen "?"-Knopf auf jedem Bildschirm.' }
    },

    'playbook': {
      es: { titulo:'Playbook',
        que:'Las jugadas del equipo, dibujadas, para que las vean los jugadores.',
        pasos:['Tocá una jugada para verla en grande.','Está pensado para que el jugador la repase en su celular.'],
        ojo:'Esto lo ven los jugadores. Lo que es solo del cuerpo técnico va en Game Plan.' },
      en: { titulo:'Playbook',
        que:'The team\u2019s plays, drawn out, for the players to see.',
        pasos:['Tap a play to see it full size.','Meant for players to review on their phone.'],
        ojo:'Players see this. What is staff-only goes in the Game Plan.' },
      de: { titulo:'Playbook',
        que:'Die Spielzüge des Teams, gezeichnet, für die Spieler.',
        pasos:['Tippe auf einen Spielzug, um ihn gross zu sehen.','Gedacht, damit Spieler ihn am Handy durchgehen.'],
        ojo:'Das sehen die Spieler. Was nur den Staff betrifft, steht im Game Plan.' }
    },

    'informe': {
      es: { titulo:'Informe del Partido',
        que:'El resumen de un partido, listo para leer o compartir.',
        pasos:['Elegí el partido.','Mirá los números por set y por fundamento.'],
        ojo:'Para el análisis profundo están los mapas de calor y el plan de partido.' },
      en: { titulo:'Match Report',
        que:'The summary of a match, ready to read or share.',
        pasos:['Pick the match.','Look at the numbers by set and by skill.'],
        ojo:'For deeper analysis use the heat maps and the match plan.' },
      de: { titulo:'Spielbericht',
        que:'Die Zusammenfassung eines Spiels, bereit zum Lesen oder Teilen.',
        pasos:['Wähle das Spiel.','Sieh die Zahlen nach Satz und Element.'],
        ojo:'Für tiefere Analysen gibt es die Heatmaps und den Spielplan.' }
    },

    'diagnostico': {
      es: { titulo:'Diagnóstico',
        que:'Revisa que los datos de la app estén completos y sin errores.',
        pasos:['Se llena solo al abrir.','Si algo falta, lo dice con su nombre.'],
        ojo:'Es una pantalla de servicio: si dice que todo está en orden, no hay nada que hacer.' },
      en: { titulo:'Diagnostics',
        que:'Checks that the app\u2019s data is complete and error-free.',
        pasos:['It fills itself when opened.','If something is missing, it names it.'],
        ojo:'This is a service screen: if it says everything is fine, there is nothing to do.' },
      de: { titulo:'Diagnose',
        que:'Prüft, ob die Daten der App vollständig und fehlerfrei sind.',
        pasos:['Sie füllt sich beim Öffnen von selbst.','Fehlt etwas, wird es benannt.'],
        ojo:'Ein Servicebildschirm: steht dort, dass alles in Ordnung ist, gibt es nichts zu tun.' }
    },

    'index': {
      es: { titulo:'Inicio',
        que:'La puerta de entrada: desde acá se llega a todo lo que hace la app.',
        pasos:['Elegí la categoría arriba si el club tiene varias.','Tocá la tarjeta de lo que necesites.','El próximo partido aparece destacado arriba.'],
        ojo:'Los jugadores ven solo las tarjetas que les corresponden. El cuerpo técnico ve todas.' },
      en: { titulo:'Home',
        que:'The way in: everything the app does is reachable from here.',
        pasos:['Pick the category at the top if the club has several.','Tap the card for what you need.','The next match is highlighted at the top.'],
        ojo:'Players only see the cards meant for them. The staff sees all of them.' },
      de: { titulo:'Start',
        que:'Der Einstieg: von hier aus ist alles erreichbar, was die App kann.',
        pasos:['Wähle oben die Kategorie, wenn der Verein mehrere hat.','Tippe auf die Kachel, die du brauchst.','Das nächste Spiel wird oben hervorgehoben.'],
        ojo:'Spieler sehen nur die für sie bestimmten Kacheln. Der Staff sieht alle.' }
    },

    'ranking': {
      es: { titulo:'Ranking',
        que:'Cómo está cada jugador del plantel comparado con los demás.',
        pasos:['Elegí el fundamento arriba.','La lista se ordena de mejor a peor.'],
        ojo:'Mirá el volumen además del puesto: el que jugó tres partidos no se compara con el que jugó veinte.' },
      en: { titulo:'Ranking',
        que:'How each player in the squad stands against the rest.',
        pasos:['Choose the skill at the top.','The list sorts from best to worst.'],
        ojo:'Look at the volume as well as the position: three matches does not compare with twenty.' },
      de: { titulo:'Rangliste',
        que:'Wie jeder Spieler des Kaders im Vergleich zu den anderen dasteht.',
        pasos:['Wähle oben das Element.','Die Liste sortiert von best nach schlechtest.'],
        ojo:'Achte neben der Platzierung auf das Volumen: drei Spiele sind nicht mit zwanzig vergleichbar.' }
    },

    'recepcion': {
      es: { titulo:'Recepción',
        que:'Quién recibe, desde dónde le sacan y con qué calidad.',
        pasos:['Elegí el jugador o mirá el equipo completo.','Las zonas muestran desde dónde le llegan los saques.','Filtrá por rival para preparar el próximo partido.'],
        ojo:'El porcentaje que importa es el de recepción positiva (#+): es la que deja armar.' },
      en: { titulo:'Reception',
        que:'Who passes, where the serves come from, and with what quality.',
        pasos:['Pick the player or look at the whole team.','The zones show where the serves reach them from.','Filter by opponent to prepare the next match.'],
        ojo:'The percentage that matters is positive reception (#+): that is the one that lets you set.' },
      de: { titulo:'Annahme',
        que:'Wer annimmt, woher aufgeschlagen wird und in welcher Qualität.',
        pasos:['Wähle den Spieler oder sieh das ganze Team.','Die Zonen zeigen, woher die Aufschläge kommen.','Filtere nach Gegner, um das nächste Spiel vorzubereiten.'],
        ojo:'Entscheidend ist die positive Annahme (#+): sie ermöglicht das Zuspiel.' }
    },

    'tendencias': {
      es: { titulo:'Tendencias',
        que:'Cómo evoluciona el equipo partido a partido.',
        pasos:['Elegí el fundamento.','La línea muestra si sube o baja a lo largo de la temporada.'],
        ojo:'Un partido malo no es una tendencia. Mirá la dirección de tres o cuatro seguidos.' },
      en: { titulo:'Trends',
        que:'How the team evolves match by match.',
        pasos:['Choose the skill.','The line shows whether it rises or falls across the season.'],
        ojo:'One bad match is not a trend. Look at the direction across three or four in a row.' },
      de: { titulo:'Trends',
        que:'Wie sich das Team von Spiel zu Spiel entwickelt.',
        pasos:['Wähle das Element.','Die Linie zeigt, ob es über die Saison steigt oder fällt.'],
        ojo:'Ein schlechtes Spiel ist kein Trend. Achte auf die Richtung über drei bis vier Spiele.' }
    },

    'videos': {
      es: { titulo:'Videos Destacados',
        que:'Las jugadas que el cuerpo técnico eligió guardar.',
        pasos:['Tocá un video para verlo.','Sirve para la charla técnica y para mostrarle a un jugador algo puntual.'],
        ojo:'Para buscar jugadas por acción y valoración está Cortes de Video.' },
      en: { titulo:'Featured Videos',
        que:'The rallies the coaching staff chose to keep.',
        pasos:['Tap a video to watch it.','Useful for the team talk and to show a player something specific.'],
        ojo:'To search rallies by action and grade, use Video Clips.' },
      de: { titulo:'Ausgewählte Videos',
        que:'Die Ballwechsel, die das Trainerteam behalten wollte.',
        pasos:['Tippe auf ein Video, um es anzusehen.','Nützlich für die Besprechung und um einem Spieler etwas Konkretes zu zeigen.'],
        ojo:'Um Ballwechsel nach Aktion und Bewertung zu suchen, nutze Videoclips.' }
    },

    'temporadas': {
      es: { titulo:'Temporadas',
        que:'Las temporadas anteriores, guardadas y consultables.',
        pasos:['Tocá una temporada para entrar.','Adentro está todo tal como quedó al cerrarla.'],
        ojo:'Una temporada archivada no se modifica: es una foto del momento en que se cerró.' },
      en: { titulo:'Seasons',
        que:'Previous seasons, stored and available to consult.',
        pasos:['Tap a season to open it.','Inside, everything is exactly as it was when it closed.'],
        ojo:'An archived season is never modified: it is a snapshot of the moment it was closed.' },
      de: { titulo:'Saisons',
        que:'Frühere Saisons, gespeichert und abrufbar.',
        pasos:['Tippe auf eine Saison, um sie zu öffnen.','Darin ist alles genau so, wie es beim Abschluss war.'],
        ojo:'Eine archivierte Saison wird nicht verändert: sie ist eine Momentaufnahme des Abschlusses.' }
    },

    'prep_builder': {
      es: { titulo:'Armar Rutinas',
        que:'La rutina de gimnasio que después ve cada jugador en su celular.',
        pasos:['Elegí los ejercicios de la lista.','Poné series, repeticiones y carga.','Asignásela al jugador o a todo el plantel.'],
        ojo:'Cada categoría tiene sus propias rutinas: si cambiás de categoría arriba, cambian.' },
      en: { titulo:'Build Routines',
        que:'The gym routine each player then sees on their phone.',
        pasos:['Pick the exercises from the list.','Set sets, reps and load.','Assign it to a player or to the whole squad.'],
        ojo:'Each category has its own routines: switch category at the top and they change.' },
      de: { titulo:'Routinen erstellen',
        que:'Die Kraftraum-Routine, die jeder Spieler danach am Handy sieht.',
        pasos:['Wähle die Übungen aus der Liste.','Lege Sätze, Wiederholungen und Gewicht fest.','Weise sie einem Spieler oder dem ganzen Kader zu.'],
        ojo:'Jede Kategorie hat eigene Routinen: wechselst du oben die Kategorie, ändern sie sich.' }
    },

    'calendario': {
      es: { titulo:'Calendario',
        que:'Los partidos y los entrenamientos de esta categoría, en un solo lugar.',
        pasos:['Elegí arriba si querés ver partidos o entrenamientos.','Con "+ Agregar" cargás uno a mano.','"Importar fixture" carga toda la temporada de una vez.','"Usar este fixture" hace que el próximo partido se vea en toda la app.'],
        ojo:'Cada categoría tiene su propio calendario. Si cambiás de categoría arriba, cambian los partidos.' },
      en: { titulo:'Calendar',
        que:'This category\u2019s matches and training sessions, all in one place.',
        pasos:['Choose at the top whether to see matches or training.','Use "+ Add" to enter one by hand.','"Import fixture" loads the whole season at once.','"Use this fixture" makes the next match show across the app.'],
        ojo:'Each category has its own calendar. Switch category at the top and the matches change.' },
      de: { titulo:'Kalender',
        que:'Spiele und Trainings dieser Kategorie an einem Ort.',
        pasos:['Wähle oben zwischen Spielen und Trainings.','Mit "+ Hinzufügen" trägst du eines von Hand ein.','"Spielplan importieren" lädt die ganze Saison auf einmal.','"Diesen Spielplan verwenden" zeigt das nächste Spiel in der ganzen App.'],
        ojo:'Jede Kategorie hat ihren eigenen Kalender. Wechselst du oben die Kategorie, ändern sich die Spiele.' }
    },

    'prep_fisica': {
      es: { titulo:'Preparación Física',
        que:'La carga del plantel: cuánto levanta cada uno y cómo viene.',
        pasos:['Elegí el jugador para ver su historial.','Cargá los pesos y las repeticiones de la sesión.','Mirá el wellness al lado: cómo llegó al entrenamiento.'],
        ojo:'El wellness conviene cargarlo ANTES de entrenar: sirve para decidir la sesión, no para evaluarla.' },
      en: { titulo:'Physical Preparation',
        que:'The squad\u2019s load: how much each player lifts and how they are tracking.',
        pasos:['Pick the player to see their history.','Enter the weights and reps for the session.','Check the wellness beside it: how they arrived at training.'],
        ojo:'Fill in the wellness BEFORE training: it is meant to shape the session, not to review it.' },
      de: { titulo:'Athletiktraining',
        que:'Die Belastung des Kaders: wie viel jeder hebt und wie er dasteht.',
        pasos:['Wähle den Spieler, um seinen Verlauf zu sehen.','Trage Gewichte und Wiederholungen der Einheit ein.','Sieh daneben das Wellness: wie er ins Training kam.'],
        ojo:'Wellness VOR dem Training ausfüllen: es soll die Einheit steuern, nicht bewerten.' }
    },

    'pizarron': {
      es: { titulo:'Pizarrón',
        que:'La cancha para dibujar jugadas y explicarlas al plantel.',
        pasos:['Arrastrá los jugadores a su posición.','Dibujá los movimientos con el dedo o el mouse.','Guardá la jugada para volver a mostrarla.'],
        ojo:'Sirve en la tablet del banco: se dibuja durante el partido y se muestra en el tiempo muerto.' },
      en: { titulo:'Tactical Board',
        que:'The court to draw plays and explain them to the squad.',
        pasos:['Drag the players into position.','Draw the movements with your finger or the mouse.','Save the play to show it again.'],
        ojo:'Works on the bench tablet: draw during the match and show it in the timeout.' },
      de: { titulo:'Taktiktafel',
        que:'Das Feld zum Zeichnen von Spielzügen und Erklären im Kader.',
        pasos:['Ziehe die Spieler auf ihre Positionen.','Zeichne die Bewegungen mit Finger oder Maus.','Speichere den Spielzug, um ihn erneut zu zeigen.'],
        ojo:'Funktioniert auf dem Tablet der Bank: während des Spiels zeichnen und in der Auszeit zeigen.' }
    },

    'equipo': {
      es: { titulo:'El Plantel',
        que:'Todos los jugadores de esta categoría, con su puesto y su dorsal.',
        pasos:['Tocá un jugador para ver su perfil completo.','El color indica el puesto: armador, central, punta, opuesto, líbero.','Abajo está el cuerpo técnico: tocá "+ Agregar" para sumar a alguien.'],
        ojo:'El plantel sale de los partidos scouteados. Si falta alguien, es que todavía no jugó.' },
      en: { titulo:'The Squad',
        que:'Every player in this category, with their position and shirt number.',
        pasos:['Tap a player to see their full profile.','The colour shows the position: setter, middle, outside, opposite, libero.'],
        ojo:'The squad comes from the scouted matches. If someone is missing, they have not played yet.' },
      de: { titulo:'Der Kader',
        que:'Alle Spieler dieser Kategorie mit Position und Trikotnummer.',
        pasos:['Tippe auf einen Spieler für sein vollständiges Profil.','Die Farbe zeigt die Position: Zuspieler, Mitte, Aussen, Diagonal, Libero.'],
        ojo:'Der Kader stammt aus den gescouteten Spielen. Fehlt jemand, hat er noch nicht gespielt.' }
    },

    'comparador': {
      es: { titulo:'Comparador',
        que:'Dos jugadores lado a lado, fundamento por fundamento.',
        pasos:['Elegí los dos jugadores arriba.','Compará cada fundamento: quién ataca mejor, quién recibe mejor.'],
        ojo:'Fijate el volumen además del porcentaje: 60% con 5 pelotas no dice lo mismo que 45% con 300.' },
      en: { titulo:'Comparator',
        que:'Two players side by side, skill by skill.',
        pasos:['Pick the two players at the top.','Compare each skill: who attacks better, who passes better.'],
        ojo:'Look at the volume as well as the percentage: 60% off 5 balls is not the same as 45% off 300.' },
      de: { titulo:'Vergleich',
        que:'Zwei Spieler nebeneinander, Element für Element.',
        pasos:['Wähle oben die beiden Spieler.','Vergleiche jedes Element: wer greift besser an, wer nimmt besser an.'],
        ojo:'Achte neben der Prozentzahl auf das Volumen: 60% bei 5 Bällen ist nicht wie 45% bei 300.' }
    },

    'scouting_rival': {
      es: { titulo:'Scouting del Rival',
        que:'El resumen del próximo rival, listo para la charla técnica.',
        pasos:['Elegí el equipo rival.','Mirá sus jugadoras clave y por dónde atacan.','Bajalo o mostralo directo en la reunión.'],
        ojo:'Sale de los partidos de ese rival que ya tengas scouteados. Cuantos más, más confiable.' },
      en: { titulo:'Opponent Scouting',
        que:'The next opponent\u2019s summary, ready for the team talk.',
        pasos:['Pick the opposing team.','Look at their key players and where they attack.','Download it or show it straight in the meeting.'],
        ojo:'It comes from the matches of that opponent you already scouted. The more, the more reliable.' },
      de: { titulo:'Gegner-Scouting',
        que:'Die Zusammenfassung des nächsten Gegners, bereit für die Besprechung.',
        pasos:['Wähle die gegnerische Mannschaft.','Sieh dir die Schlüsselspieler an und wohin sie angreifen.','Lade sie herunter oder zeige sie direkt in der Besprechung.'],
        ojo:'Sie stammt aus den bereits gescouteten Spielen dieses Gegners. Je mehr, desto verlässlicher.' }
    },

    'informe_equipo': {
      es: { titulo:'Informe de Equipo',
        que:'Cómo viene el equipo en el total de la temporada.',
        pasos:['Mirá el cambio de saque y el break point contra lo esperado.','Compará con los partidos anteriores para ver la tendencia.'],
        ojo:'El "esperado" es el promedio de la liga. Estar debajo en una sola cosa no es grave; estar debajo en todas, sí.' },
      en: { titulo:'Team Report',
        que:'How the team is tracking across the whole season.',
        pasos:['Check side-out and break point against what is expected.','Compare with previous matches to see the trend.'],
        ojo:'"Expected" is the league average. Being below in one area is not serious; being below in all of them is.' },
      de: { titulo:'Mannschaftsbericht',
        que:'Wie das Team über die ganze Saison dasteht.',
        pasos:['Prüfe Side-out und Break Point gegenüber dem Erwartungswert.','Vergleiche mit früheren Spielen, um den Trend zu sehen.'],
        ojo:'"Erwartet" ist der Ligadurchschnitt. In einem Bereich darunter ist nicht schlimm, in allen schon.' }
    },

    'nla_stats_table': {
      es: { titulo:'Estadísticas de la Liga',
        que:'Todos los jugadores de la liga, ordenables por cualquier columna.',
        pasos:['Elegí el fundamento arriba.','Tocá una columna para ordenar por ahí.','Usá los filtros para ver un equipo o un puesto.'],
        ojo:'"Solo la liga" deja afuera a los rivales de copa y a los de muy pocas acciones, que distorsionan el ranking.' },
      en: { titulo:'League Statistics',
        que:'Every player in the league, sortable by any column.',
        pasos:['Choose the skill at the top.','Tap a column to sort by it.','Use the filters to see one team or one position.'],
        ojo:'"League only" leaves out cup opponents and players with very few actions, which distort the ranking.' },
      de: { titulo:'Ligastatistik',
        que:'Alle Spieler der Liga, nach jeder Spalte sortierbar.',
        pasos:['Wähle oben das Element.','Tippe auf eine Spalte, um danach zu sortieren.','Nutze die Filter für ein Team oder eine Position.'],
        ojo:'"Nur Liga" blendet Pokalgegner und Spieler mit sehr wenigen Aktionen aus, die die Rangliste verzerren.' }
    },

    'game_plan': {
      es: { titulo:'Game Plan',
        que:'El plan escrito para el partido: lo que se decide en la semana.',
        pasos:['Escribí las consignas por fundamento.','Guardalo y queda disponible para todo el cuerpo técnico.'],
        ojo:'Lo ve el staff, no los jugadores. Para lo que ellos tienen que saber está el Playbook.' },
      en: { titulo:'Game Plan',
        que:'The written plan for the match: what gets decided during the week.',
        pasos:['Write the instructions by skill.','Save it and it becomes available to the whole staff.'],
        ojo:'The staff sees it, not the players. For what they need to know there is the Playbook.' },
      de: { titulo:'Spielplan',
        que:'Der schriftliche Matchplan: was in der Woche entschieden wird.',
        pasos:['Schreibe die Vorgaben nach Element.','Speichere ihn und er steht dem ganzen Staff zur Verfügung.'],
        ojo:'Der Staff sieht ihn, nicht die Spieler. Für sie gibt es das Playbook.' }
    },

    'plan_desarrollo': {
      es: { titulo:'Plan de Desarrollo',
        que:'En qué está trabajando cada jugador y cómo viene.',
        pasos:['Elegí el jugador.','Definí el objetivo y las semanas.','El jugador lo ve en su propio perfil.'],
        ojo:'Un objetivo por vez funciona mejor que cinco a la vez.' },
      en: { titulo:'Development Plan',
        que:'What each player is working on and how it is going.',
        pasos:['Pick the player.','Set the goal and the number of weeks.','The player sees it in their own profile.'],
        ojo:'One goal at a time works better than five at once.' },
      de: { titulo:'Entwicklungsplan',
        que:'Woran jeder Spieler arbeitet und wie es läuft.',
        pasos:['Wähle den Spieler.','Lege das Ziel und die Wochen fest.','Der Spieler sieht es in seinem eigenen Profil.'],
        ojo:'Ein Ziel nach dem anderen funktioniert besser als fünf gleichzeitig.' }
    },

    'horarios': {
      es: { titulo:'Horarios',
        que:'Los entrenamientos de la semana de esta categoría.',
        pasos:['Cargá el día, la hora y el lugar.','Queda visible para todo el plantel.'],
        ojo:'Cada categoría tiene sus propios horarios: si cambiás de categoría arriba, cambian.' },
      en: { titulo:'Schedule',
        que:'This category\u2019s training sessions for the week.',
        pasos:['Enter the day, time and place.','It becomes visible to the whole squad.'],
        ojo:'Each category has its own schedule: switch category at the top and it changes.' },
      de: { titulo:'Zeitplan',
        que:'Die Trainingseinheiten dieser Kategorie für die Woche.',
        pasos:['Trage Tag, Uhrzeit und Ort ein.','Er wird für den ganzen Kader sichtbar.'],
        ojo:'Jede Kategorie hat ihren eigenen Zeitplan: wechselst du oben, ändert er sich.' }
    },

    'importar_video': {
      es: { titulo:'Cargar Videos',
        que:'Enganchar el video de un partido para que se abran los cortes.',
        pasos:['Elegí el partido.','Pegá el link de YouTube.','Ajustá el segundo en que empieza el primer punto.'],
        ojo:'Si la cámara cortó el partido en varios archivos, unilos antes con Unir Videos: los cortes necesitan uno solo.' },
      en: { titulo:'Load Videos',
        que:'Link a match video so the clips can open.',
        pasos:['Pick the match.','Paste the YouTube link.','Set the second where the first point starts.'],
        ojo:'If the camera split the match into several files, merge them first: the clips need a single file.' },
      de: { titulo:'Videos laden',
        que:'Ein Spielvideo verknüpfen, damit die Clips sich öffnen.',
        pasos:['Wähle das Spiel.','Füge den YouTube-Link ein.','Stelle die Sekunde ein, in der der erste Punkt beginnt.'],
        ojo:'Hat die Kamera das Spiel geteilt, füge die Dateien vorher zusammen: die Clips brauchen eine einzige.' }
    },

    'baggerone': {
      es: { titulo:'Baggerone',
        que:'El juego interno del plantel: quién suma y cómo va la tabla.',
        pasos:['Cargá los resultados de cada ronda.','La tabla se ordena sola.'],
        ojo:'Cada categoría tiene su propia tabla.' },
      en: { titulo:'Baggerone',
        que:'The squad\u2019s internal game: who scores and how the table looks.',
        pasos:['Enter the results of each round.','The table sorts itself.'],
        ojo:'Each category has its own table.' },
      de: { titulo:'Baggerone',
        que:'Das interne Spiel des Kaders: wer punktet und wie die Tabelle aussieht.',
        pasos:['Trage die Ergebnisse jeder Runde ein.','Die Tabelle sortiert sich selbst.'],
        ojo:'Jede Kategorie hat ihre eigene Tabelle.' }
    },

    'camara': {
      es: { titulo:'Cámara',
        que:'Transmite lo que filma un celular a donde estés scouteando, con retraso.',
        pasos:['En el celular que filma, abrí esta pantalla y creá la sala. Te da un código.',
               'Donde scouteás, entrá a Scout en Vivo, tocá Video y poné ese código.',
               'El retraso se elige ahí, no en el celular: hay un deslizador de 0 a 25 segundos.',
               'Arranca en 0 —o sea, en directo—. Subilo al empezar el partido para tener margen.',
               '"Ver último punto" repite el rally que acaba de cerrar, sin mover el deslizador.'],
        ojo:'Los dos aparatos tienen que estar en la misma red. Si el wifi se corta, hay que volver a poner el código de sala: el scouteo sigue igual, solo se pierde el video.' },
      en: { titulo:'Camera',
        que:'Streams what a phone films to wherever you are scouting, with a delay.',
        pasos:['On the filming phone, open this screen and create the room. It gives you a code.',
               'Where you scout, open Live Scout, tap Video and enter that code.',
               'The delay is set there, not on the phone: a slider from 0 to 25 seconds.',
               'It starts at 0 —live—. Raise it when the match begins so you have margin.',
               '"Watch last point" replays the rally that just ended, without moving the slider.'],
        ojo:'Both devices must be on the same network. If the wifi drops, you have to enter the room code again: scouting carries on, only the video is lost.' },
      de: { titulo:'Kamera',
        que:'Überträgt das Handybild mit Verzögerung dorthin, wo du scoutest.',
        pasos:['Öffne auf dem filmenden Handy diesen Bildschirm und erstelle den Raum. Du bekommst einen Code.',
               'Öffne beim Scouten das Live-Scouting, tippe auf Video und gib den Code ein.',
               'Die Verzögerung stellst du dort ein, nicht am Handy: ein Regler von 0 bis 25 Sekunden.',
               'Er startet bei 0 —live—. Erhöhe ihn zu Spielbeginn, um Spielraum zu haben.',
               '"Letzten Punkt ansehen" wiederholt den eben beendeten Ballwechsel.'],
        ojo:'Beide Geräte müssen im selben Netz sein. Bricht das WLAN ab, muss der Raumcode neu eingegeben werden: das Scouting läuft weiter, nur das Video fehlt.' }
    },

    'sesiones': {
      es: { titulo:'Sesiones y Accesos',
        que:'Quién entró a la app y desde qué aparato.',
        pasos:['Revisá la lista si sospechás que alguien entró sin permiso.','Podés cerrar una sesión a distancia.'],
        ojo:'Si un jugador se va del club, cerrale la sesión acá.' },
      en: { titulo:'Sessions and Access',
        que:'Who logged into the app and from which device.',
        pasos:['Check the list if you suspect someone got in without permission.','You can close a session remotely.'],
        ojo:'If a player leaves the club, close their session here.' },
      de: { titulo:'Sitzungen und Zugänge',
        que:'Wer sich in der App angemeldet hat und von welchem Gerät.',
        pasos:['Prüfe die Liste, wenn du unbefugten Zugriff vermutest.','Du kannst eine Sitzung aus der Ferne beenden.'],
        ojo:'Verlässt ein Spieler den Verein, beende hier seine Sitzung.' }
    },

    'panel_voley': {
      es: { titulo:'Panel del Partido',
        que:'El partido en vivo visto desde el banco: los números que van saliendo.',
        pasos:['Se llena solo mientras el asistente scoutea.','Mirá las baterías y las rotaciones durante el partido.'],
        ojo:'Necesita que alguien esté scouteando en vivo desde Scout en Vivo.' },
      en: { titulo:'Match Panel',
        que:'The live match seen from the bench: the numbers as they come in.',
        pasos:['It fills itself while the assistant scouts.','Watch the target bars and rotations during the match.'],
        ojo:'It needs someone scouting live from Live Scout.' },
      de: { titulo:'Spiel-Panel',
        que:'Das Livespiel von der Bank aus: die Zahlen, während sie entstehen.',
        pasos:['Es füllt sich von selbst, während der Assistent scoutet.','Beobachte Zielbalken und Rotationen während des Spiels.'],
        ojo:'Es braucht jemanden, der live über Live-Scouting scoutet.' }
    },

    'hm_defensa': {
      es: { titulo:'Mapa de Defensa',
        que:'Dónde levanta cada jugador y desde dónde le atacan.',
        pasos:['Elegí el jugador y el rival.','Las zonas más calientes son donde más pelotas le llegan.'],
        ojo:'Doble click en una zona abre el video de esas defensas.' },
      en: { titulo:'Defence Map',
        que:'Where each player digs and where the attacks come from.',
        pasos:['Pick the player and the opponent.','The hottest zones are where most balls reach them.'],
        ojo:'Double-click a zone to open the video of those digs.' },
      de: { titulo:'Abwehrkarte',
        que:'Wo jeder Spieler abwehrt und woher die Angriffe kommen.',
        pasos:['Wähle Spieler und Gegner.','Die heissesten Zonen sind, wo die meisten Bälle ankommen.'],
        ojo:'Doppelklick auf eine Zone öffnet das Video dieser Abwehraktionen.' }
    },

    'hm_bloqueo': {
      es: { titulo:'Mapa de Bloqueo',
        que:'Dónde bloquea cada jugador y con qué resultado.',
        pasos:['Elegí el jugador.','Mirá en qué zona bloquea más y dónde le pasan.'],
        ojo:'El bloqueo se lee siempre del archivo scouteado, no del video: los números son exactos.' },
      en: { titulo:'Block Map',
        que:'Where each player blocks and with what outcome.',
        pasos:['Pick the player.','See which zone they block most and where they get beaten.'],
        ojo:'Blocking is always read from the scouted file, not the video: the numbers are exact.' },
      de: { titulo:'Blockkarte',
        que:'Wo jeder Spieler blockt und mit welchem Ergebnis.',
        pasos:['Wähle den Spieler.','Sieh, in welcher Zone er am meisten blockt und wo er überwunden wird.'],
        ojo:'Der Block wird immer aus der gescouteten Datei gelesen, nicht aus dem Video: die Zahlen stimmen exakt.' }
    },

    'plan_partido': {
      es: {
        titulo: 'Plan de Partido',
        que: 'Todo lo que necesitás saber del próximo rival, armado solo con los partidos que ya scouteaste.',
        pasos: [
          'Elegí el equipo rival arriba a la izquierda.',
          'Filtrá por partido si querés ver solo algunos, o dejá "todos" para la temporada entera.',
          'Cambiá de pestaña según lo que busques: direcciones de ataque, distribución del armador, zonas de recepción, saque, defensa o bloqueo.',
          'Cada jugador tiene sus filtros propios: por combinación, fase, tipo de recepción y resultado.',
          'Doble click en cualquier zona y se abre el video de esas jugadas.'
        ],
        ojo: 'Los números son golpes, no puntos. El porcentaje de al lado es la eficacia.'
      },
      en: {
        titulo: 'Match Plan',
        que: 'Everything you need to know about the next opponent, built automatically from the matches you already scouted.',
        pasos: [
          'Pick the opposing team at the top left.',
          'Filter by match to see only some, or leave "all" for the whole season.',
          'Switch tabs depending on what you need: attack directions, setter distribution, reception zones, serve, defence or block.',
          'Each player has their own filters: by combination, phase, reception type and outcome.',
          'Double-click any zone to open the video of those rallies.'
        ],
        ojo: 'The numbers are attempts, not points. The percentage next to them is efficiency.'
      },
      de: {
        titulo: 'Spielplan',
        que: 'Alles über den nächsten Gegner, automatisch aus den bereits gescouteten Spielen erstellt.',
        pasos: [
          'Wähle oben links die gegnerische Mannschaft.',
          'Filtere nach Spiel, um nur einzelne zu sehen, oder lasse "alle" für die ganze Saison.',
          'Wechsle die Registerkarte je nach Bedarf: Angriffsrichtungen, Zuspielverteilung, Annahmezonen, Aufschlag, Abwehr oder Block.',
          'Jeder Spieler hat eigene Filter: nach Kombination, Phase, Annahmeart und Ergebnis.',
          'Doppelklick auf eine Zone öffnet das Video dieser Ballwechsel.'
        ],
        ojo: 'Die Zahlen sind Schläge, keine Punkte. Der Prozentsatz daneben ist die Effizienz.'
      }
    },

    'alta_jugadores': {
      es: {
        titulo: 'Alta de Jugadores',
        que: 'Les da acceso a la app: cada jugador entra con su cuenta y ve solo lo suyo.',
        pasos: [
          'Si el club tiene varias categorías, elegí arriba a cuál van estos jugadores.',
          'Completá cada fila: número de camiseta, mail y fecha de nacimiento.',
          'Tocá el círculo del final para agregar la foto. Es opcional.',
          'Agregá tantas filas como jugadores tengas.',
          'Tocá "Revisar y continuar" y después "Crear las cuentas".'
        ],
        ojo: 'La contraseña de cada jugador es su fecha de nacimiento, en formato ddmmaaaa. La puede cambiar después.'
      },
      en: {
        titulo: 'Add Players',
        que: 'Gives players access to the app: each one logs in and sees only their own data.',
        pasos: [
          'If the club has several categories, pick at the top which one these players belong to.',
          'Fill in each row: shirt number, email and date of birth.',
          'Tap the circle at the end to add a photo. Optional.',
          'Add as many rows as you have players.',
          'Tap "Review and continue", then "Create the accounts".'
        ],
        ojo: 'Each player\u2019s password is their date of birth as ddmmyyyy. They can change it later.'
      },
      de: {
        titulo: 'Spieler anlegen',
        que: 'Gibt den Spielern Zugang zur App: jeder meldet sich an und sieht nur seine eigenen Daten.',
        pasos: [
          'Hat der Verein mehrere Kategorien, wähle oben, zu welcher diese Spieler gehören.',
          'Fülle jede Zeile aus: Trikotnummer, E-Mail und Geburtsdatum.',
          'Tippe auf den Kreis am Ende, um ein Foto hinzuzufügen. Optional.',
          'Füge so viele Zeilen hinzu, wie du Spieler hast.',
          'Tippe auf "Prüfen und weiter" und dann auf "Konten erstellen".'
        ],
        ojo: 'Das Passwort jedes Spielers ist sein Geburtsdatum als TTMMJJJJ. Es kann später geändert werden.'
      }
    },

    'cortes': {
      es: {
        titulo: 'Cortes de Video',
        que: 'Las jugadas que buscás, una atrás de otra, en el segundo exacto del contacto.',
        pasos: [
          'Elegí el equipo y la temporada.',
          'Elegí los partidos: todos, o solo los que te interesan.',
          'Marcá las acciones que querés ver. El número al lado dice cuántas hay de cada una.',
          'Tocá "Reproducir" y se van pasando solas.'
        ],
        ojo: 'Con Z volvés 2 segundos, con X adelantás, con R repetís el clip. Loop lo deja repitiendo.'
      },
      en: {
        titulo: 'Video Clips',
        que: 'The rallies you are looking for, one after another, at the exact moment of contact.',
        pasos: [
          'Pick the team and the season.',
          'Pick the matches: all of them, or only the ones you care about.',
          'Tick the actions you want to see. The number beside each says how many there are.',
          'Tap "Play" and they run one after the other.'
        ],
        ojo: 'Z goes back 2 seconds, X skips forward, R repeats the clip. Loop keeps it repeating.'
      },
      de: {
        titulo: 'Videoclips',
        que: 'Die gesuchten Ballwechsel, einer nach dem anderen, genau im Moment des Kontakts.',
        pasos: [
          'Wähle Mannschaft und Saison.',
          'Wähle die Spiele: alle oder nur die gewünschten.',
          'Markiere die Aktionen, die du sehen willst. Die Zahl daneben zeigt, wie viele es gibt.',
          'Tippe auf "Abspielen" und sie laufen nacheinander.'
        ],
        ojo: 'Z springt 2 Sekunden zurück, X vorwärts, R wiederholt den Clip. Loop wiederholt dauerhaft.'
      }
    },

    'panel_vivo': {
      es: {
        titulo: 'Scout en Vivo',
        que: 'Scouteás el partido mientras se juega, con el video al lado y las estadísticas calculándose solas.',
        pasos: [
          'Cargá los dos equipos y sus jugadores antes de empezar.',
          'Poné el video: podés usar la cámara con retraso para revisar la jugada que se te pasó.',
          'Tipeá cada acción con el teclado, igual que en DataVolley.',
          'Mirá las baterías y las direcciones actualizándose durante el partido.',
          'Al terminar, guardá el archivo. Abre en DataVolley sin convertir nada.'
        ],
        ojo: 'Tipeá la S cuando el jugador LANZA la pelota, no cuando la golpea: así lo calcula el algoritmo de sincronización y los cortes de video quedan en el segundo justo. Y antes de guardar, pasá el verificador de códigos.'
      },
      en: {
        titulo: 'Live Scout',
        que: 'Scout the match as it is played, with the video beside you and the stats updating on their own.',
        pasos: [
          'Load both teams and their players before starting.',
          'Set up the video: you can use the delayed camera to review a rally you missed.',
          'Type each action with the keyboard, the same way as in DataVolley.',
          'Watch the target bars and directions update during the match.',
          'When you finish, save the file. It opens in DataVolley with no conversion.'
        ],
        ojo: 'Before saving, run the code checker: it flags what does not add up, while there is still time to fix it.'
      },
      de: {
        titulo: 'Live-Scouting',
        que: 'Scoute das Spiel während es läuft, mit Video daneben und Statistiken, die sich selbst berechnen.',
        pasos: [
          'Lade beide Mannschaften und ihre Spieler vor dem Start.',
          'Richte das Video ein: mit der verzögerten Kamera kannst du verpasste Ballwechsel prüfen.',
          'Tippe jede Aktion mit der Tastatur, genau wie in DataVolley.',
          'Beobachte, wie sich Zielbalken und Richtungen während des Spiels aktualisieren.',
          'Speichere am Ende die Datei. Sie öffnet sich in DataVolley ohne Umwandlung.'
        ],
        ojo: 'Vor dem Speichern den Code-Prüfer laufen lassen: er markiert Unstimmigkeiten, solange noch Zeit zur Korrektur ist.'
      }
    },

    'analisis': {
      es: {
        titulo: 'Análisis',
        que: 'Cómo viene el equipo contra los objetivos que fijó el club, y jugador por jugador.',
        pasos: [
          'Elegí si querés ver partidos, entrenamientos o todo junto.',
          'Mirá las baterías del equipo: cada una es un objetivo.',
          'Verde llegó, ámbar está cerca, rojo está lejos.',
          'Abajo está el mismo tablero para cada jugador del plantel.'
        ],
        ojo: 'Los objetivos los define el club y se cambian en la configuración. No son fijos.'
      },
      en: {
        titulo: 'Analysis',
        que: 'How the team is tracking against the club\u2019s targets, and player by player.',
        pasos: [
          'Choose whether to look at matches, training sessions, or both.',
          'Check the team bars: each one is a target.',
          'Green reached it, amber is close, red is far off.',
          'Below you get the same board for every player in the squad.'
        ],
        ojo: 'The targets are set by the club and can be changed in the settings. They are not fixed.'
      },
      de: {
        titulo: 'Analyse',
        que: 'Wie das Team im Vergleich zu den Vereinszielen dasteht, und Spieler für Spieler.',
        pasos: [
          'Wähle, ob du Spiele, Trainings oder beides sehen willst.',
          'Sieh dir die Team-Balken an: jeder ist ein Ziel.',
          'Grün erreicht, Bernstein nah dran, Rot weit entfernt.',
          'Darunter findest du dieselbe Übersicht für jeden Spieler des Kaders.'
        ],
        ojo: 'Die Ziele legt der Verein fest und können in den Einstellungen geändert werden. Sie sind nicht fix.'
      }
    }

  };

  /* ── Que pantalla es esta ─────────────────────────────────────────────── */
  function pantalla() {
    var p = (location.pathname || '').split('/').pop() || '';
    p = p.replace(/\.html.*$/, '').toLowerCase();

    /* ── LA RAIZ ES EL INICIO ──────────────────────────────────────────
       El link que se comparte es "gelp-voley.vercel.app/" a secas, sin
       decir index.html. Ahi el nombre queda vacio y no aparecia el boton
       justo en la primera pantalla que ve todo el mundo. */
    if (!p) p = 'index';

    /* ── LOS ARCHIVOS QUE LLEVAN EL NOMBRE DEL CLUB ────────────────────
       Algunas pantallas se llaman con el club adentro, porque se generan
       para cada uno: "Team_Playbook_Nafels.html", "MANUAL_GELP_VOLEY.html".
       El nombre cambia en cada club, asi que la clave del diccionario no
       puede coincidir nunca.

       Se reconocen por lo que tienen en comun: la palabra clave adentro. */
    if (p.indexOf('playbook') >= 0) return 'playbook';
    if (p.indexOf('manual') >= 0)   return 'manual';

    return p;
  }


  /* ── Que idioma esta puesto ───────────────────────────────────────────── */
  function idioma() {
    try {
      if (window.getLang) return window.getLang();
      return localStorage.getItem('vb_lang') || 'es';
    } catch (e) { return 'es'; }
  }

  function texto() {
    var a = AYUDA[pantalla()];
    if (!a) return null;
    return a[idioma()] || a.es || null;
  }

  /* ── El cartel ────────────────────────────────────────────────────────── */
  var CERRAR = { es: 'Entendido', en: 'Got it', de: 'Verstanden' };

  function abrir() {
    var d = texto();
    if (!d) return;

    var fondo = document.createElement('div');
    fondo.id = 'ayuda-fondo';
    fondo.style.cssText =
      'position:fixed;inset:0;z-index:99999;background:rgba(3,7,18,.78);' +
      'backdrop-filter:blur(4px);display:flex;align-items:center;' +
      'justify-content:center;padding:20px;animation:ayFade .18s ease';

    var pasos = (d.pasos || []).map(function (p, i) {
      return '<li style="display:flex;gap:11px;padding:8px 0;' +
             'border-bottom:1px solid rgba(255,255,255,.06);line-height:1.55">' +
             '<span style="flex:none;width:21px;height:21px;border-radius:6px;' +
             'background:rgba(230,167,67,.13);border:1px solid rgba(230,167,67,.3);' +
             'color:#e6a743;font-size:11px;font-weight:700;display:flex;' +
             'align-items:center;justify-content:center;margin-top:1px">' +
             (i + 1) + '</span><span>' + p + '</span></li>';
    }).join('');

    fondo.innerHTML =
      '<div style="max-width:520px;width:100%;max-height:84vh;overflow:auto;' +
      'background:#0e1524;border:1px solid rgba(255,255,255,.1);border-radius:16px;' +
      'padding:26px;box-shadow:0 24px 70px rgba(0,0,0,.6)">' +

        '<div style="display:flex;align-items:flex-start;gap:12px;margin-bottom:14px">' +
          '<div style="flex:none;width:34px;height:34px;border-radius:10px;' +
          'background:rgba(230,167,67,.13);border:1px solid rgba(230,167,67,.3);' +
          'display:flex;align-items:center;justify-content:center;font-size:17px">?</div>' +
          '<div style="flex:1;min-width:0">' +
            '<div style="font-size:19px;font-weight:800;line-height:1.2">' +
              (d.titulo || '') + '</div>' +
          '</div>' +
          '<button id="ayuda-x" aria-label="Cerrar" style="flex:none;width:30px;height:30px;' +
          'border-radius:8px;cursor:pointer;background:transparent;' +
          'border:1px solid rgba(255,255,255,.1);color:#8da0bc;font-size:15px">\u00d7</button>' +
        '</div>' +

        '<p style="color:#93a5c0;font-size:14.5px;line-height:1.6;margin:0 0 18px">' +
          (d.que || '') + '</p>' +

        '<ul style="list-style:none;margin:0 0 18px;padding:0;font-size:14px">' +
          pasos + '</ul>' +

        (d.ojo ?
          '<div style="background:rgba(230,167,67,.08);' +
          'border:1px solid rgba(230,167,67,.25);border-radius:10px;padding:12px 14px;' +
          'font-size:13.5px;line-height:1.55;color:#e8d4b0">' + d.ojo + '</div>'
          : '') +

        '<button id="ayuda-ok" style="width:100%;margin-top:18px;padding:12px;' +
        'border-radius:9px;border:none;cursor:pointer;background:#e6a743;' +
        'color:#150500;font-weight:700;font-size:14.5px">' +
          (CERRAR[idioma()] || CERRAR.es) + '</button>' +
      '</div>';

    function cerrar() {
      if (fondo.parentNode) fondo.parentNode.removeChild(fondo);
      document.removeEventListener('keydown', esc);
    }
    function esc(e) { if (e.key === 'Escape') cerrar(); }

    fondo.addEventListener('click', function (e) { if (e.target === fondo) cerrar(); });
    document.addEventListener('keydown', esc);
    document.body.appendChild(fondo);
    var x = document.getElementById('ayuda-x');
    var ok = document.getElementById('ayuda-ok');
    if (x) x.onclick = cerrar;
    if (ok) ok.onclick = cerrar;
  }

  /* ── El boton ─────────────────────────────────────────────────────────── */
  function poner() {
    if (!texto()) return;                       // sin ayuda escrita, sin boton
    if (document.getElementById('ayuda-btn')) return;

    var b = document.createElement('button');
    b.id = 'ayuda-btn';
    b.type = 'button';
    b.textContent = '?';
    b.setAttribute('aria-label', 'Ayuda');
    b.title = { es: '¿Cómo funciona esta pantalla?',
                en: 'How does this screen work?',
                de: 'Wie funktioniert dieser Bildschirm?' }[idioma()] || 'Ayuda';
    /* ── DONDE VA ─────────────────────────────────────────────────────
       El chat ya ocupa la esquina de abajo a la derecha: un circulo de
       46px en bottom:22 right:24, y su globito de aviso sube hasta 72px.
       El "?" se pone ARRIBA del chat, alineado al mismo eje, para que no
       se pisen ni en el celular.
       Si en alguna pantalla no hay chat, queda igual de comodo. */
    b.style.cssText =
      'position:fixed;right:26px;bottom:80px;z-index:8999;width:40px;height:40px;' +
      'border-radius:50%;cursor:pointer;background:rgba(230,167,67,.14);' +
      'border:1px solid rgba(230,167,67,.4);color:#e6a743;font-size:19px;' +
      'font-weight:800;line-height:1;box-shadow:0 6px 20px rgba(0,0,0,.35);' +
      'transition:transform .15s,background .15s';
    b.onmouseenter = function () {
      b.style.transform = 'translateY(-2px)';
      b.style.background = 'rgba(230,167,67,.22)';
    };
    b.onmouseleave = function () {
      b.style.transform = '';
      b.style.background = 'rgba(230,167,67,.14)';
    };
    b.onclick = abrir;
    document.body.appendChild(b);
  }

  /* si cambian el idioma, se actualiza el globito y lo que este abierto */
  window.addEventListener('langchange', function () {
    var b = document.getElementById('ayuda-btn');
    if (b) {
      b.title = { es: '¿Cómo funciona esta pantalla?',
                  en: 'How does this screen work?',
                  de: 'Wie funktioniert dieser Bildschirm?' }[idioma()] || 'Ayuda';
    }
    var f = document.getElementById('ayuda-fondo');
    if (f) { f.parentNode.removeChild(f); abrir(); }
  });

  var css = document.createElement('style');
  css.textContent = '@keyframes ayFade{from{opacity:0}to{opacity:1}}' +
                    '@media print{#ayuda-btn{display:none}}';
  document.head.appendChild(css);

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', poner);
  } else {
    poner();
  }

  window.abrirAyuda = abrir;      // por si se quiere llamar desde otro boton
})();
