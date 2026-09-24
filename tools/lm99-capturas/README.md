# Capturas de Lecturameter 1999 sin emulador

Herramienta usada el 24-09-2026 para renderizar las capturas de `capturas-1999/` a partir del
codigo real de `lecturameter-rebuilds/lm-1999` (Compose Multiplatform) en un target JVM, sin
Android SDK ni emulador. Renderiza `App(store)` con `ImageComposeScene` a 1080x2400 (densidad 2.625)
y permite tocar, arrastrar, hacer scroll y teclear por linea de comandos.

## Piezas

- `lm99desktop/`: proyecto Gradle (Kotlin 2.2.10, CMP 1.7.3). `commonMain` apunta al `commonMain`
  real de `lm-1999` (sustituir `REBUILDS_REPO` por la ruta del clon de `lecturameter-rebuilds`).
  `src/jvmMain` contiene los `actual` de escritorio (ficheros, imagenes, red, sin pickers) y el driver `shot/Main.kt`.
- `lm99desktop/shim-*`: androidx.collection, annotation, arch.core y lifecycle compilados desde el fuente
  de `github.com/androidx/androidx` (sparse checkout de `collection/collection`, `annotation/annotation`,
  `arch/core/core-common`, `lifecycle/lifecycle-{common,runtime,viewmodel}`; sustituir `ANDROIDX_SRC`).
  Solo hacen falta donde Google Maven este bloqueado; con acceso a Google Maven se pueden borrar los
  `shim-*`, sus `include` en `settings.gradle.kts` y el bloque `dependencySubstitution` de `build.gradle.kts`.
  En `shim-lifecycle-runtime` y `shim-lifecycle-viewmodel` las fuentes se copian (no se enlazan) para
  reemplazar `LifecycleTracer.jvmAndAndroid.kt` por la variante `nonJvm` y evitar `androidx.tracing`.
- `seed.py`: genera un directorio de datos con `data.json` (FullBackup v10), `timer.json` y `local.json`
  con 7 clasicos de dominio publico y 39 sesiones. Modos: `normal` (crono corriendo), `notimer`, `tips`
  (globos sin ver). Las portadas se descargan de Standard Ebooks (`raw.githubusercontent.com/standardebooks/<slug>/master/images/cover.jpg`).

## Uso

```bash
python3 seed.py /tmp/lm99data notimer
gradle packageUberJarForCurrentOS
java -Djava.awt.headless=true -jar build/compose/jars/lm99desktop-linux-x64-1.0.0.jar \
  /tmp/lm99data 2.625 1080 2400 wait:800 tap:46,518 wait:800 shot:/tmp/biblioteca.png
```

Acciones (coordenadas en dp): `tap:x,y`, `long:x,y`, `drag:x1,y1,x2,y2`, `scroll:x,y,n`, `type:texto`,
`wait:ms`, `shot:ruta.png`. Coordenadas usadas para las nueve capturas: iconos de la barra de
herramientas a y=84 (nuevo 20, propiedades 54, borrar 85, play 124, pausa 156, stop 187, informe 225,
historial 258); fila de Dracula en la tabla (46,518); boton minimizar del crono (275,352).

Para que el texto salga en Roboto como en Android hay que instalar Roboto y preferirlo en fontconfig
para `sans-serif` (`~/.config/fontconfig/fonts.conf`). Sin eso Skia usa DejaVu Sans.
