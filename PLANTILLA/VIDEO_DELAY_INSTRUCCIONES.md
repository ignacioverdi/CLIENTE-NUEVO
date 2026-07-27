# 📹 VIDEO EN VIVO CON DELAY — Cómo usarlo

Basado en el manual DataVolley (§3.1 Capture, §3.2 Streaming, §5 Web Client):
el scout conecta una cámara y vos en la tablet ves el video con delay + el replay del último punto.
Todo por la misma red WiFi, sin instalar nada, sin servidores.

---

## ARCHIVOS A SUBIR

### {{CLUB}} (repo {{CLUB_REPO}})
- `camara_{{CLUB}}.html`      → subir como  **camara.html**
- `video_delay_{{CLUB}}.js`   → subir como  **video_delay.js**
- `panel_voley_{{CLUB}}.html` → subir como  **panel_voley.html**  (ya trae el botón 📹 Video)

### {{CLUB}} (repo Voley-Stats)
- `camara_{{CLUB}}.html`       → subir como  **camara.html**
- `video_delay_{{CLUB}}.js`    → subir como  **video_delay.js**
- `panel_voley_{{CLUB}}.html`  → subir como  **panel_voley.html**

---

## CÓMO SE USA (en el partido)

1. **En el celular** (el que apunta a la cancha, en trípode):
   - Abrí `{{DOMINIO}}/camara.html`
   - Elegí la cámara y la calidad (Alta 720p va perfecto)
   - Tocá **▶ Transmitir**
   - Aparece un **código de sala de 4 dígitos** (ej: 3721)
   - Dejá esa pantalla abierta y el celu enchufado

2. **En la tablet** (panel_voley):
   - Tocá el botón **📹 Video**
   - Escribí el código de sala (3721)
   - Tocá **Conectar**

3. **Ya lo ves con delay.** Tenés:
   - **Deslizador de Delay** (0 a 25 seg): elegís cuánto atrás querés ver la acción
   - **Botón "↺ Ver último punto"**: reproduce los últimos ~12 segundos (el rally que acaba de pasar)

---

## NOTAS IMPORTANTES

- **Todos en la misma red WiFi** (celu, scout, tablet). Es lo que lo hace simple y rápido.
- Si no conecta: revisá que el celu esté transmitiendo y que el código sea el correcto.
- El celu puede reemplazarse por: la webcam de la PC, o OBS (con cámara virtual del navegador).
- **HTTPS obligatorio**: como está en Vercel (https), la cámara funciona. En http local no.
- Permiso de cámara: la primera vez el navegador del celu va a pedir permiso → Permitir.

---

## LO QUE ES HONESTO DECIR

- El **"último punto" es lo más sólido y fluido** — ideal para revisar el error que acaba de pasar.
- El **delay continuo** funciona, pero puede tener algún pequeño salto según el equipo/WiFi
  (es una limitación del video en navegador, no de una app de escritorio como DataVolley).
- Si el delay continuo no se ve fluido en tu equipo, usá delay 0 (vivo directo) + el botón de último punto,
  que es la combinación más confiable.

---

## PENDIENTE / A PROBAR (cuando vuelvas)

1. Subir los archivos y probar la conexión real celu ↔ tablet en tu WiFi.
2. Ver si el delay continuo se ve fluido en tu tablet; si no, ajustamos (bajar calidad o usar solo replay).
3. OPCIONAL futuro: conectar el botón "último punto" automáticamente con el cierre de rally del scout
   (el scout ya publica _rallyN; se puede marcar el punto exacto en el buffer). Quedó la base lista.
