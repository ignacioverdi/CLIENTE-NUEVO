/* datos_prep_fisica.js — la preparación física.

   Vacío hasta que el club procese su primer partido: ahí se llena
   solo. Existe desde el arranque porque las pantallas lo piden, y
   sin el archivo se rompen enteras en vez de mostrarse sin datos.

   La FORMA importa: la lista tiene que existir aunque no tenga a
   nadie. Un objeto pelado rompe igual que la falta del archivo. */
window.PREP_DATA = { generado: "", jugadores: [] };
