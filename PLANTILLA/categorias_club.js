/* ═══════════════════════════════════════════════════════════════════════════
   categorias_club.js — LAS CATEGORIAS QUE TIENE ESTE CLUB

   Un club puede tener un solo equipo o toda la estructura formativa. Cada
   categoria es un equipo distinto: sus partidos, sus jugadoras y sus numeros
   no se mezclan con los de otra —el porcentaje de ataque de una Sub-16 al
   lado del de Primera no significa nada—.

   ── COMO SE USA ──────────────────────────────────────────────────────────
   Si el club tiene UNA sola categoria, se deja como esta: la app no muestra
   ningun selector y todo funciona como siempre.

   Si tiene varias, se escriben aca:

       window.CATEGORIAS_CLUB = ['Primera', 'Sub-21', 'Sub-18', 'Sub-16'];

   Desde ese momento:
     · al subir un partido se elige a que categoria pertenece
     · cada una guarda sus datos por separado
     · la app deja cambiar de categoria con un clic

   La primera de la lista es la que se abre por defecto.
   ═══════════════════════════════════════════════════════════════════════════ */

window.CATEGORIAS_CLUB = ['Primera'];

/* © 2025-2026 Ignacio Verdi · {{CLUB}} VOLEY · Software propietario */
