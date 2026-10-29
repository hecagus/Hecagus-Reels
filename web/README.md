# HEC REELS · estudio web

Sitio: https://hecagus-reels.vercel.app

Escribe una idea o un guion, genera la voz con Piper en español mexicano y renderiza desde GitHub Actions. Hay dos motores:
- **2.5D (predeterminado):** Pillow + FFmpeg, bajo consumo.
- **Blender 3D (experimental):** escenas 3D procedurales **distintas según palabras clave del guion** (terminales de pago, redes, comida, motocicletas y nube), renderizadas con Cycles CPU. `scene_director.py` elige una plantilla visual permitida para cada escena y `compose_3d.py` la monta usando los tiempos reales de la narración Piper. Si no reconoce el tema usa geometría genérica. **No es generación libre con IA**, no hay sincronización labial ni escenas fotorrealistas. Puede consumir más minutos de Actions que el motor 2.5D.

## Sin introducir claves en la página

Se eliminó el campo «Clave privada del estudio», «Comprobar clave» y «Mostrar clave».
El estudio usa **inicio de sesión con GitHub**, autorizado únicamente para la cuenta **hecagus**. Se guarda una cookie de sesión firmada, Secure, SameSite=Lax, HttpOnly, que expira a los 7 días; el token privado no se envía al navegador.

La página sigue siendo pública para editar ideas y usar el generador gratuito por plantillas. Para ejecutar Actions, consultar renders o usar una API de IA con costo, es obligatorio iniciar sesión como propietario. Si aún no configuraste GitHub OAuth, puedes abrir **GitHub Actions (manual)** e iniciar el workflow directamente dentro de GitHub, con tu cuenta. En la ejecución manual, el campo de narración debe contener el texto separado por `||`.

### Configuración en GitHub (una vez)

1. Abre GitHub → Settings → Developer settings → OAuth Apps → New OAuth App.
2. Application name: `HEC REELS Studio`.
3. Homepage URL: `https://hecagus-reels.vercel.app`.
4. Authorization callback URL: `https://hecagus-reels.vercel.app/api/callback`.
5. Copia el **Client ID** y crea un **Client secret**. No los compartas públicamente.

En el proyecto Vercel `hecagus-reels`, Root Directory `web`, configura variables privadas en **Production**:

| Variable | Propósito |
| --- | --- |
| `GITHUB_TOKEN` | Token fino con alcance solo a `hecagus/Hecagus-Reels`, Actions: Read and write, usado por Vercel para iniciar workflows y listar artifacts |
| `GITHUB_OAUTH_CLIENT_ID` | Identificador público de la OAuth App |
| `GITHUB_OAUTH_CLIENT_SECRET` | Secreto privado de la OAuth App; nunca en JS del cliente |
| `HEC_SESSION_SECRET` | Recomendado: secreto aleatorio largo para firmar cookies y URLs de descarga |
| `OPENAI_API_KEY` | Opcional, para creación automática de guiones mediante API de pago |
| `OPENAI_MODEL` | Opcional, modelo disponible según tarifas de la API |

Si no defines `HEC_SESSION_SECRET`, el servidor usa `GITHUB_TOKEN` como secreto de firma hasta que configures uno independiente. **Nunca introduces esos valores en la web.** La antigua variable `HEC_ACCESS_KEY` ya no se utiliza y se puede borrar de Vercel después de desplegar esta versión.

**Importante:** vuelve a desplegar Production después de editar las variables. Hasta que GitHub OAuth esté configurado, el botón «Entrar con GitHub» permanece oculto y se ofrece la opción manual en GitHub Actions. No se abre el endpoint con tu `GITHUB_TOKEN` a visitantes anónimos.

## Seguridad y límites

- Los secretos permanecen en Vercel; nunca uses `NEXT_PUBLIC_` / `VITE_` para ellos.
- La cuenta autorizada se valida consultando la identidad real de GitHub en el callback, no por un nombre escrito en el navegador.
- Los endpoints de inicio de workflow, consulta de trabajos y guiones con IA exigen cookie firmada de propietario.
- Las URLs de descarga se firman por dos minutos; los artifacts duran siete días.
- El repositorio es público: no introduzcas datos privados en títulos de ejecución o narraciones.
- Esta demo todavía no dispone de cola ni límite de frecuencia persistente. El acceso solo para el propietario reduce la exposición, pero un control de cuota sigue siendo recomendable.
- `blender_scene.py` solo ofrece cinco categorías de objetos (más el modo genérico). Es una primera biblioteca de plantillas, no comprensión general del guion. Las categorías y sus palabras clave se pueden ampliar en `scene_director.py` tras pruebas.

## Desarrollo y pruebas

```bash
cd web
npm test
```

El workflow `.github/workflows/verificar-web.yml` comprueba sintaxis de los endpoints y pruebas de seguridad. `.github/workflows/smoke-blender.yml` verifica imágenes de dos categorías y la composición H.264/AAC con una pista de audio simulada. La validación completa exige ejecutar **Generar reel con Piper es-MX** con `estilo=3d` y comprobar el audio Piper real. La prueba simulada no equivale a escuchar la voz.


## Generación autónoma con Gemini Omni Flash (experimental)

Página: https://hecagus-reels.vercel.app/omni.html

Esta función es independiente del motor gratuito Piper. Recibe una idea de 8-350 caracteres, crea un guion JSON con Gemini 2.5 Flash, solicita clips con Gemini Omni Flash y usa FFmpeg en GitHub Actions para normalizar 6 segundos por escena y ensamblar un MP4 9:16 con audio.

### Configuración mínima (sin pegar claves en la web)

1. En Google AI Studio crea una API key de un proyecto con **facturación habilitada** y acceso al modelo **gemini-omni-1.1-flash**. La suscripción de Gemini para consumidores no incluye automáticamente los cargos de esta API.
2. En GitHub abre hecagus/Hecagus-Reels → Settings → Secrets and variables → Actions → New repository secret. Nombre exacto: **GEMINI_API_KEY**. Su valor nunca se coloca en el código ni en Vercel.
3. Conserva la configuración de GitHub OAuth y GITHUB_TOKEN en Vercel descrita arriba. La web autoriza únicamente a la cuenta hecagus; si no está habilitado OAuth, ejecuta el workflow manual **HEC REELS - Video IA Gemini Omni**.
4. Elige una prueba de **6 segundos** antes del video completo de **60 segundos**. Marca el consentimiento de gasto. No hay generación ni cargos automáticos al publicar esta actualización.

**Costos y límites:** El precio efectivo publicado de Omni a 720p es aproximadamente US$0.10 por segundo generado, más guion y posibles intentos fallidos. Son referencias aproximadas de US$0.60/6s y US$6/60s si la duración realmente generada coincide con la montada. Los clips de Omni pueden durar de 3 a 10 s; el montaje ajusta cada clip a 6 s y puede congelar el último fotograma cuando sea más corto. No hay reintentos automáticos que vuelvan a cobrar. La factura real depende de tokens de salida, duración efectiva y tarifas vigentes. El guion/archivo son visibles a quien acceda al artifact con autorización; el repo y las entradas de Actions pueden ser públicos.

**Limitaciones:** No se admite aún fotografía de referencia desde la web. Los personajes se describen en los prompts y su continuidad no está garantizada. Gemini Omni puede fallar con voces en español mexicano o sincronía labial. Si una escena carece de audio o video, el workflow falla y no afirma haber entregado un MP4. El resultado se descarga desde la sección "Mis videos Omni" en un archivo ZIP con MP4, portada y guion. Las ejecuciones están serializadas por cuenta. Los artifacts expiran en 7 días.

Código: omni_producer.py, .github/workflows/generar-omni.yml, web/api/omni.js, web/omni.html.

Documentación Google: https://ai.google.dev/gemini-api/docs/omni y https://ai.google.dev/gemini-api/docs/pricing.
