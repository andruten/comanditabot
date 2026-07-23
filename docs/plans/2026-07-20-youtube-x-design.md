# YouTube y X design

Comandita aceptará enlaces públicos de YouTube con los formatos `youtube.com/shorts/<id>`, `youtube.com/watch?v=<id>` y `youtu.be/<id>`. Los vídeos de YouTube se limitarán a diez minutos: yt-dlp descartará el enlace durante la extracción de metadatos, antes de descargar sus archivos. Si el servicio no expone una duración, se aplicará el mismo descarte preventivo. El resto de plataformas no tendrá este límite de duración nuevo.

Los enlaces de YouTube aprobados conservan el flujo existente: descarga temporal, límite de tamaño, generación opcional de miniatura y respuesta adjunta al mensaje de origen. El bot registrará un aviso claro cuando descarte un vídeo por duración sin incluir consultas o fragmentos de URL en los logs.

Para X y Twitter, la imagen instalará `curl-cffi` y el extractor configurará la impersonación de Chrome exclusivamente para esos dominios. Así yt-dlp puede solicitar los recursos de vídeo públicos con una huella de navegador compatible con los requisitos actuales de X. No se añadirán cookies, credenciales, sesiones ni soporte para contenido privado. El error de descarga seguirá produciendo la respuesta breve actual al usuario.

Las pruebas cubrirán la clasificación de cada URL de YouTube, el filtro de duración de YouTube, el rechazo seguro de duración desconocida y la configuración exclusiva de la impersonación de X. Tras las pruebas del contenedor, se construirá la imagen desde esta rama y se publicará mediante la actualización GitOps existente.
