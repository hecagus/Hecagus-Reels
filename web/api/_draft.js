/**
 * Borradores SIN IA generativa. No llama modelos ni servicios externos.
 * Ajustar las escenas a hechos verificables y revisar antes de publicar.
 */
const common = [
  { pattern: /bases?\s+de\s+datos|\bdatabase\b|\bsql\b|\bmysql\b|\bpostgres(?:ql)?\b/i,
    topic: 'Bases de datos',
    scenes: [
      'Una base de datos organiza información para guardarla, consultarla y actualizarla.',
      'Por ejemplo, una tienda registra productos, clientes y ventas en distintas tablas.',
      'Cada registro reúne datos específicos, como un nombre, un precio o una fecha.',
      'Las consultas permiten encontrar información sin revisar los registros uno por uno.',
      'También importan los respaldos, los permisos de acceso y la consistencia de los datos.'
    ] },
  { pattern: /\bdns\b|sistema\s+de\s+nombres?\s+de\s+dominio/i,
    topic: 'DNS',
    scenes: [
      'El DNS ayuda a encontrar la dirección IP asociada con un nombre de dominio.',
      'Cuando escribes una dirección web, tu equipo consulta cómo localizar ese dominio.',
      'Si la información no está en caché, se realizan otras consultas para resolver el nombre.',
      'Con la dirección obtenida, el navegador puede iniciar la conexión con el servidor.',
      'DNS no entrega el contenido del sitio. Su función principal es resolver nombres.'
    ] },
  { pattern: /\bnube\b|\bcloud\b|google cloud|computaci[oó]n\s+en\s+la\s+nube/i,
    topic: 'Computación en la nube',
    scenes: [
      'La nube permite utilizar servidores y servicios informáticos a través de internet.',
      'En lugar de comprar toda la infraestructura, puedes contratar recursos según la necesidad.',
      'Un ejemplo es alojar una aplicación y almacenar sus archivos en un proveedor de nube.',
      'Los costos dependen del consumo, la configuración y los servicios contratados.',
      'También debes revisar seguridad, respaldos y disponibilidad antes de elegir.'
    ] },
  { pattern: /\bredes\b|\brouter\b|\bwi-?fi\b|\binternet\b|\benrutador\b/i,
    topic: 'Redes',
    scenes: [
      'Una red permite que dispositivos compartan información mediante conexiones y protocolos.',
      'En casa, el router conecta tu red local con otras redes, incluido internet.',
      'Los dispositivos utilizan direcciones IP para identificar el origen y destino de los datos.',
      'Wi-Fi es una forma de conexión inalámbrica, pero también puedes utilizar cables.',
      'Para encontrar una falla, revisa primero la conexión, la IP y la ruta hacia el destino.'
    ] },
  { pattern: /\bpresupuesto\b|\bfinanzas\b|\bgastos\b|\bingresos\b|\bahorro\b/i,
    topic: 'Presupuesto',
    scenes: [
      'Un presupuesto sirve para planear qué hacer con tus ingresos y gastos.',
      'Empieza registrando cuánto dinero entra y cuáles pagos tienen una fecha comprometida.',
      'Separa los gastos necesarios, las deudas y las metas de ahorro.',
      'Compara lo planeado con los movimientos reales, sin contar ingresos que aún no recibes.',
      'Actualizarlo cada semana te ayuda a detectar cambios antes de quedarte sin liquidez.'
    ] },
  { pattern: /inteligencia\s+artificial|\bIA\b|\bmachine learning\b|aprendizaje\s+autom[aá]tico/i,
    topic: 'Inteligencia artificial',
    scenes: [
      'La inteligencia artificial agrupa técnicas para que sistemas realicen tareas complejas.',
      'Algunos modelos aprenden patrones a partir de datos para producir predicciones o respuestas.',
      'Un ejemplo es clasificar mensajes o transcribir una grabación automáticamente.',
      'Sus resultados pueden contener errores; conviene verificar los datos importantes.',
      'Antes de usarla, revisa privacidad, calidad de los datos y límites del modelo.'
    ] },
  { pattern: /\bpython\b|\bjavascript\b|\bprogramaci[oó]n\b|\bc[oó]digo\b/i,
    topic: 'Programación',
    scenes: [
      'Programar consiste en escribir instrucciones para que una computadora haga una tarea.',
      'Una aplicación recibe datos, realiza operaciones y presenta un resultado.',
      'Por ejemplo, un formulario puede enviar información a un servidor para guardarla.',
      'Las pruebas ayudan a detectar errores antes de publicar los cambios.',
      'El código debe ser comprensible, verificable y fácil de mantener.'
    ] },
  { pattern: /ciberseguridad|\bcontrase[nñ]as?\b|\bseguridad inform[aá]tica\b/i,
    topic: 'Ciberseguridad',
    scenes: [
      'La ciberseguridad busca reducir riesgos para sistemas, dispositivos e información.',
      'Usar contraseñas únicas y autenticación en dos pasos protege mejor las cuentas.',
      'Actualizar aplicaciones y sistemas corrige vulnerabilidades conocidas.',
      'Los respaldos permiten recuperar información ante errores o ataques.',
      'Ninguna medida garantiza seguridad absoluta: conviene combinar varias defensas.'
    ] }
];

function normal(text) { return text.trim().replace(/\s+/g,' ').normalize('NFC'); }
export function buildDraft(idea) {
  if (typeof idea !== 'string') throw new Error('Escribe un tema para el reel.');
  const clean=normal(idea);
  if(clean.length<3||clean.length>350) throw new Error('Escribe una idea de 3 a 350 caracteres.');
  const entry=common.find(x=>x.pattern.test(clean));
  let scenes;
  let topic;
  if (entry) {
    scenes=entry.scenes;
    topic=entry.topic;
  } else {
    topic=clean.length>55?clean.slice(0,52).trimEnd()+'…':clean;
    scenes=[
      'Hoy vamos a hablar de '+topic+'. Empecemos por definir de qué se trata.',
      'Primero identifica para qué se utiliza y qué problema busca resolver.',
      'Después busca un ejemplo concreto: qué información entra y qué resultado se obtiene.',
      'Antes de aplicarlo, revisa las ventajas, los límites y la información disponible.',
      'Este es un borrador inicial: agrega datos comprobados antes de publicar el video.'
    ];
  }
  if (scenes.some(s=>s.length<2||s.length>105||s.split(/\s+/).some(w=>w.length>30)))
    throw new Error('La plantilla sobrepasó los límites del editor.');
  return {topic,scenes, texto:scenes.join(' || '), source:'plantilla',isAI:false};
}
