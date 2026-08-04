#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
actualizar_temporadas.py  <id-temporada>
Agrega una temporada archivada a la lista de temporadas.js (idempotente).
Lo llama ARCHIVAR_TEMPORADA.bat; normalmente no se corre a mano.
Ej:  python actualizar_temporadas.py 2025-26
"""
import sys, io, os

if len(sys.argv) < 2:
    print("Falta el id de temporada (ej: 2025-26)"); sys.exit(1)

sid = sys.argv[1].strip()
label = sid.replace('-', '/')
F = 'temporadas.js'
MARKER = '<<TEMPORADAS>>'

if not os.path.exists(F):
    print(f"[ATENCION] No encuentro {F} en esta carpeta; no registro el menú.")
    sys.exit(0)

s = io.open(F, encoding='utf-8').read()

if f'id:"{sid}"' in s or f"id:'{sid}'" in s:
    print(f"   La temporada {sid} ya estaba registrada en el menú. OK.")
    sys.exit(0)

lines = s.splitlines(keepends=True)
out = []
inserted = False
entry = f'  {{ id:"{sid}", label:"{label}" }},\n'
for ln in lines:
    if (MARKER in ln) and not inserted:
        out.append(entry)
        inserted = True
    out.append(ln)

if not inserted:
    print(f"[ATENCION] No encontré la marca {MARKER} en {F}. Agregá a mano: {entry.strip()}")
    sys.exit(0)

io.open(F, 'w', encoding='utf-8').write(''.join(out))
print(f"   Temporada {sid} registrada en el menú (temporadas.js).")

# © 2025-2026 Ignacio Verdi · NAFELS VOLEY · Software propietario - Todos los derechos reservados
