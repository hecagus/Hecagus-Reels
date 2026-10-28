# HecAgus Reels (HEC REELS) · Estudio web

Página para crear videos verticales sin instalar aplicaciones.

## Cómo funciona

1. La persona escribe un guion o una idea en la web.
2. **Idea sin IA:** sin contratar ninguna API, un generador determinista de plantillas temáticas escribe 5 escenas editables. Es un borrador inicial, no una respuesta de inteligencia artificial; requiere revisión manual. **IA opcional:** solo si configuras `OPENAI_API_KEY`, un modelo de OpenAI genera el guion.
3. **Generar:** Vercel recibe las escenas y usa el token privado de GitHub para iniciar el workflow.
4. GitHub Actions instala Piper y FFmpeg en el servidor, sintetiza la voz \`es_MX-claude-high\` y genera el MP4.
5. La web consulta las ejecuciones y permite descargar un ZIP con MP4, portada y subtítulos. Artifacts duran 7 días.

**Importante:** la web NO genera clips de video fotorrealistas ni fondos ilustrados únicos: usa las animaciones procedurales 2.5D existentes. Sin una API de IA configurada, también puedes generar un borrador gratuito por plantillas desde un tema como «Base de datos».

## Despliegue en Vercel

Crea un proyecto conectado a \`hecagus/Hecagus-Reels\`, con **Root Directory = web**, sin framework y sin build command.

En Settings → Environment Variables configura:

- \`GITHUB_TOKEN\`: token fino de GitHub, limitado exclusivamente a \`hecagus/Hecagus-Reels\`, con permiso de repositorio **Actions: Read and write** (y Metadata read que GitHub agrega). Guardarlo como variable privada. No colocarlo en GitHub ni en el navegador.
- \`HEC_ACCESS_KEY\`: frase aleatoria privada de **16 o más caracteres**, distinta del token anterior. La persona solo introduce esta clave de acceso en la web, no el token de GitHub. Guardarla como variable privada.
- \`OPENAI_API_KEY\` (opcional): cambia el botón **Crear guion gratis (plantilla)** por **Crear guion con IA**. Usa una clave de API propia, no la suscripción de ChatGPT; genera cargos por consumo. Configura presupuestos/límites en tu cuenta de API.
- \`OPENAI_MODEL\` (opcional): por defecto \`gpt-5-mini\`; se recomienda cambiarlo según disponibilidad y tarifas del proveedor.

Vuelve a desplegar después de agregar las variables. Evita copiar secrets en commits o mensajes.

## Limitaciones y seguridad

- El repositorio es público; evita enviar información privada en títulos de ejecución, prompts o narraciones. El contenido puede ser visible en GitHub Actions según permisos y registro.
- Los links de descarga de la aplicación son firmados y duran dos minutos. Si caducan, pulsa actualizar para generar otro.
- No hay almacenamiento de claves del usuario en localStorage: permanecen solo en el campo del navegador mientras la pestaña esté abierta.
- Un usuario que conozca \`HEC_ACCESS_KEY\` puede gastar minutos de GitHub Actions y llamadas a OpenAI (si está configurado). Protege la clave y configura topes presupuestarios.
- No uses \`NEXT_PUBLIC_\` ni \`VITE_\` para los secretos: quedarían expuestos al cliente.
- La interfaz consulta el estado de GitHub; no ejecuta Piper ni instala dependencias en el móvil.
- Este prototipo no tiene base de datos ni cola de trabajos propia. El historial proviene de GitHub Actions y cada archivo expira según su retención.
- Se recomienda un sistema real de login y rate limiting antes de compartir la web públicamente.

## Desarrollo

\`\`\`bash
cd web
npm test
\`\`\`

No son necesarias dependencias npm para la interfaz y las funciones básicas.
