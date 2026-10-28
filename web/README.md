# HEC REELS · estudio web

Sitio: https://hecagus-reels.vercel.app

Escribe una idea o un guion, genera la voz con Piper en español mexicano y renderiza desde GitHub Actions. Hay dos motores:
- **2.5D (predeterminado):** Pillow + FFmpeg, bajo consumo.
- **Blender 3D (experimental):** escena 3D procedural con personaje estilizado y cubo animado, renderizada con Cycles CPU. El clip 3D se repite para cubrir la narración de Piper. Todavía NO representa visualmente las ideas de cada guion, no tiene sincronización labial ni genera escenas fotorrealistas. Puede tardar más y consumir minutos de Actions.

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
- `blender_scene.py` es una escena genérica: para reels que expliquen conceptos concretos será necesario traducir el guion a objetos y animaciones específicas.

## Desarrollo y pruebas

```bash
cd web
npm test
```

El workflow `.github/workflows/verificar-web.yml` comprueba sintaxis de los endpoints y pruebas de seguridad. Para verificar Blender realmente hay que ejecutar **Generar reel con Piper es-MX** en GitHub Actions con `estilo=3d` y comprobar el MP4 y el artifact. Una comprobación de sintaxis por sí sola no garantiza el render 3D.
