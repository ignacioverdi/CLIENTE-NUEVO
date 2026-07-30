/* datos_videos.js — los videos por jugador.

   Vacío hasta que el club procese su primer partido: ahí se llena
   solo. Existe desde el arranque porque las pantallas lo piden, y
   sin el archivo se rompen enteras en vez de mostrarse sin datos.

   La FORMA importa: la lista tiene que existir aunque no tenga a
   nadie. Un objeto pelado rompe igual que la falta del archivo. */
window.VIDEOS_DATA = { generado: "", jugadores: [] };
