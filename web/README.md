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
- \`HEC_ACCESS_KEY\`: secreto del servidor de **16 o más caracteres**, distinto del token anterior. Se conserva para firmar enlaces de descarga; **ya no se escribe en la web**.
- \`OPENAI_API_KEY\` (opcional): cambia el botón **Crear guion gratis (plantilla)** por **Crear guion con IA**. Usa una clave de API propia, no la suscripción de ChatGPT; genera cargos por consumo. Configura presupuestos/límites en tu cuenta de API.
- \`OPENAI_MODEL\` (opcional): por defecto \`gpt-5-mini\`; se recomienda cambiarlo según disponibilidad y tarifas del proveedor.

**Configuración imprescindible antes de activar esta versión:**
1. En Vercel → Project Settings → Deployment Protection, activa **Vercel Authentication para todos los despliegues (All Deployments)**, no solo Preview.
2. Comprueba en Project Settings que la protección figure activa para Production, incluyendo el dominio `hecagus-reels.vercel.app`.
3. Solo después configura `HEC_AUTH_MODE=vercel` en Production mediante variables de entorno y realiza un nuevo despliegue.
4. Para publicar estos cambios en `main`, verifica antes el control de acceso anterior. Si está desactivado, **no publiques** la versión sin contraseña.

La protección es obligatoria porque los endpoints usan el token de GitHub desde el servidor. `HEC_AUTH_MODE` es un seguro para evitar habilitar renders antes de configurar Vercel Authentication; no verifica la identidad por sí solo.

Si Vercel Authentication no está disponible en tu plan, conserva la versión actual con contraseña y no actives este cambio.

## Limitaciones y seguridad

- El repositorio es público; evita enviar información privada en títulos de ejecución, prompts o narraciones. El contenido puede ser visible en GitHub Actions según permisos y registro.
- Los links de descarga de la aplicación son firmados y duran dos minutos. Si caducan, pulsa actualizar para generar otro.
- No se solicita clave de estudio en la página: Vercel exige iniciar sesión antes de mostrarla. El token de GitHub y el secreto para firmar descargas permanecen únicamente en el servidor.
- Usuarios autenticados en Vercel con acceso al proyecto pueden iniciar trabajos que consuman minutos de GitHub Actions y llamadas de API, si habilitas IA. Controla los permisos del proyecto y establece límites.
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
