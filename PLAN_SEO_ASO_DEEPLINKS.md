# Plan SEO + ASO + Deep Links — Lecturameter

> Fuente: conversación con ChatGPT (09-08-2026). Guardado por Claude para no perderlo entre sesiones.

## Idea central

No tratar SEO, ASO y deep links como 3 trabajos separados. Un solo embudo:

```
Google/Bing → web Lecturameter → Play/App Store → app → pantalla concreta
```

Mismo URL HTTPS sirve para todo (Android App Links + iOS Universal Links).

---

## Estado actual (auditado 09-08)

**Ya hecho**:
- ✅ Sitemap.xml, robots.txt
- ✅ Canonical, hreflang es/en/x-default
- ✅ Open Graph + Twitter card
- ✅ H1 único, jerarquía coherente
- ✅ HTTPS, Search Console verificado
- ✅ ES en URL separada (`/es/`), no toggle JS
- ✅ `.well-known/assetlinks.json` (hecho 08-08 con SHA-256 del keystore)
- ✅ W3C HTML 0 errores (fix 09-08)
- ✅ Todas las imgs con `alt`

**Falta**:
- Páginas de feature separadas (`/features/reading-timer`, `/cronometro-lectura`, etc.)
- `apple-app-site-association` (iOS no publicado aún)
- Contrato de URLs deep-link
- Manifest de Android con intent filters HTTPS (ahora usa `lecturameter://`)
- Investigación de keywords ES + EN para ASO
- Ficha Play Store optimizada según keywords reales

---

## Roadmap (6 fases)

### Fase 1 — SEO técnico + páginas de feature (AHORA)
- Crear 5-10 páginas de calidad, no 50 artificiales:
  - `/en/features/reading-timer/` + `/es/funciones/cronometro-lectura/`
  - `/en/features/reading-statistics/` + `/es/funciones/estadisticas-lectura/`
  - `/en/features/reading-challenges/` + `/es/funciones/retos-lectura/`
  - `/en/features/goodreads-import/` + `/es/funciones/importar-goodreads/`
- Cada página: qué hace + capturas reales + FAQ + CTA a Play Store
- hreflang entre ES/EN
- Sitemap actualizado

### Fase 2 — ASO
Hoja de keywords separada ES/EN (no traducir literal):

**España**: app para leer libros, seguimiento lectura, tracker lectura, estadísticas lectura, cronómetro lectura, control de lectura, hábitos de lectura, reto lectura

**Inglés**: reading tracker, reading log, reading timer, reading statistics, book tracker, reading habit, reading goals, reading challenges

Evitar batallas absurdas ("libros"). Long-tail con intención clara.

Ficha Play: no keywords a lo loco. Título natural: `Lecturameter - Seguimiento de lectura`. Descripción larga con keywords introducidas naturalmente.

### Fase 3 — Contrato de URLs deep-link
Definir ANTES de implementar:

| URL | Web | Android | iOS | Indexable |
|---|---|---|---|---|
| `/` | ✓ | — | — | ✓ |
| `/book/{catalogId}` | ✓ | ✓ | ✓ | ✓ |
| `/pro` | ✓ | ✓ | ✓ | ✓ |
| `/features/reading-timer` | ✓ | ✓ | ✓ | ✓ |
| `/challenge/{id}` | ✓ | ✓ | ✓ | ✓ |
| `/settings/...` | — | ✓ | ✓ | ✗ |

Empezar por `/book/{id}` porque encaja con el catálogo propio.

### Fase 4 — Android App Links
- `assetlinks.json` ya existe → sumar más packages si hace falta
- Actualizar `AndroidManifest.xml`: intent filters HTTPS para las URLs del contrato
- Navigation Compose: rutas mapeadas a las URLs
- App Links Assistant (Android Studio) + Play Console para verificar

### Fase 5 — iOS Universal Links (cuando salga iOS)
- `/.well-known/apple-app-site-association` en la web
- Associated Domains capability en Xcode
- SwiftUI navigation mapeada a las mismas URLs que Android

### Fase 6 — SEO programático selectivo (cuando haya datos)
Cuando Search Console muestre qué libros/búsquedas traen tráfico → ampliar páginas `/book/{id}` para esos títulos concretos. **NUNCA** auto-generar 2M páginas vacías.

Contenido de cada página `/book/{id}`:
- Título, autor, portada
- CTA: Registrar lectura / Cronómetro / Progreso / Estadísticas
- Botón "Añadir a biblioteca" (deep link a la app)
- Si tiene app: "Abrir en Lecturameter"
- Si no: "Descargar Lecturameter"

---

## Regla de oro

- Diseñar el contrato de URLs YA, aunque iOS no exista aún
- Implementar Android App Links primero
- Cuando llegue iOS, conectar las mismas URLs con Universal Links
- No inventar URLs distintas por plataforma

---

## Notas de contexto

- Dominio `lecturameter.com` pendiente de compra en GoDaddy. Plan de migración en `SIGUE_landing_08-08.md`.
- Actualmente en `lecturameterapp.github.io` (GitHub Pages, sin control de headers HTTP).
- Sin CDN por delante → security headers (CSP, Referrer-Policy, etc.) no accesibles sin migrar hosting.
- Repo web: `C:\Users\Víctor\lecturameterapp.github.io\`.
