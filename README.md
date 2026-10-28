# HEC REELS — versión Piper español mexicano

**Implementación original e independiente.** No se incluye código privativo de DASDINGO.

Genera videos verticales MP4, portada PNG, subtítulos SRT por escena y textos para publicación a partir de un storyboard JSON. Motor de escenas: Pillow; narración: **Piper local con modelo `es_MX-claude-high`**; render: FFmpeg. Una vez instalado y descargado el modelo, funciona sin conexión y sin API de pago.

## 1. Instalar (Windows / PowerShell)

Requiere **Windows 10/11**, Python 3.10+ y FFmpeg en PATH (`ffmpeg -version`). Windows 7 no es un objetivo compatible para esta configuración moderna. En una terminal desde la carpeta del proyecto:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m piper.download_voices es_MX-claude-high --data-dir voices
```

Si PowerShell bloquea la activación, usa los ejecutables directamente: `.venv\Scripts\python.exe -m pip install -r requirements.txt` y el mismo prefijo en los demás comandos.

## 1. Instalar (Linux / macOS)

Instala FFmpeg por el gestor de paquetes del sistema. Luego:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m piper.download_voices es_MX-claude-high --data-dir voices
```

**Nota:** el paquete `piper-tts` contiene su propio motor de fonemas. Ya **no** hace falta instalar ni ejecutar `espeak` como sintetizador separado.

El comando de descarga guarda `voices/es_MX-claude-high.onnx` y `voices/es_MX-claude-high.onnx.json` (~63 MB + configuración). El proyecto no incluye los pesos, para mantener el ZIP pequeño. También está disponible `es_MX-ald-medium`, cambiando el nombre en ambos comandos y la opción `--piper-model`.

## 2. Probar solamente la narración

```bash
python preview_voice.py --text "En HEC REELS, tus ideas se convierten en videos." --out output/prueba_piper.wav
```

## 3. Renderizar video completo

```bash
python render.py --storyboard examples/dns.json --out output/dns_piper.mp4
```

Ajustes opcionales:

```bash
python render.py --storyboard examples/dns.json --out output/dns_piper.mp4 --resolution 540x960 --fps 24 --speech-rate 1.06
```

Para usar otra voz descargada:

```bash
python render.py --storyboard examples/dns.json --out output/dns_ald.mp4 --piper-model voices/es_MX-ald-medium.onnx
```

Los archivos `dns_piper.mp4`, `dns_piper_portada.png`, `dns_piper.srt`, `dns_piper_titulo.txt` y `dns_piper_descripcion.txt` se guardan en `output/`.

## Guion y tiempos

Edita `examples/dns.json`: cada escena incluye `heading`, `text`, `voice` y `visual`. Visuales incluidos: `question`, `domain`, `resolve`, `connect` y `summary`. El render adapta cada escena a la duración real que produzca Piper; los subtítulos SRT tienen tiempo de inicio y fin por escena. **No hay subtítulos sincronizados palabra por palabra**.

`render.py` carga la voz una vez y sintetiza todos los fragmentos; después une los WAV y compone el MP4. La voz neuronal suele mejorar la entonación con respecto a eSpeak, pero la naturalidad y pronunciación deben evaluarse escuchando el modelo.

## Alcance y licencias

El código original de este ejemplo está bajo MIT. **Piper 1.8 se distribuye bajo GPL-3.0-or-later**; es una dependencia aparte, con sus propias obligaciones. El modelo `es_MX-claude-high` indica un dataset Apache-2.0 en su ficha; revisar condiciones del modelo y del dataset antes de redistribuirlos. El ZIP no redistribuye ni Piper ni sus pesos.

No se garantiza una voz indistinguible de la humana ni video 3D/fotorrealista. La fuente `203.0.113.10` del ejemplo es IP de documentación TEST-NET-3; no corresponde a `example.com` real.

## Verificación automatizada

```bash
python -m unittest discover -s tests -v
```

Las pruebas incluyen simulación de la interfaz de Piper para revisar la canalización sin descargar pesos. Una **prueba de voz real** necesita el modelo y la biblioteca instalados. En el entorno donde se preparó esta versión, la descarga externa estaba bloqueada, así que no se certificó la calidad del audio Piper.

## 4. Generar videos desde GitHub, sin instalar nada localmente

Este repositorio incluye `.github/workflows/generar-reel.yml`. Cuando el proyecto esté subido a GitHub, puedes generar un MP4 usando únicamente el navegador del celular:

1. Abre el repositorio → **Actions** → **Generar reel con Piper es-MX**.
2. Pulsa **Run workflow**, elige `texto` y escribe la narración. Para varias escenas, sepáralas con `||` (hasta 6 escenas de 105 caracteres cada una).
3. Vuelve a la ejecución completada → **Artifacts** → **HEC-REELS-...** y descarga el archivo que contiene video MP4, portada y subtítulos.

**Importante:** el texto se narra literalmente; no existe todavía un modelo de IA que redacte guiones o elija visuales según la idea. El modo `texto` usa una animación abstracta genérica, mientras que `demo_dns` reproduce el storyboard técnico del ejemplo. No hay un sitio web con un botón para generar directamente en esta versión, solo la interfaz de GitHub Actions.

GitHub Actions instalará FFmpeg y Piper y descargará la voz **en el servidor de GitHub**, no en tu equipo. Las descargas se pueden guardar en caché para siguientes ejecuciones. Por defecto, los resultados quedan como artifact 7 días.

Coste: los ejecutores estándar de GitHub Actions son gratuitos en repositorios públicos, sujetos a políticas y límites; en repositorios privados se aplican cuotas de cómputo y almacenamiento. No son una plataforma de procesamiento ilimitado ni siempre instantánea.

**Seguridad:** no pegues contraseñas, tokens ni datos personales en la narración: el texto será visible en la interfaz de ejecuciones y los logs pueden ser accesibles según visibilidad/permisos. No se necesita añadir secretos ni tokens externos.