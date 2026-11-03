export function startupError(error,{port=3000,dbPort=3306}={}){
 const messages={
  EADDRINUSE:`El puerto ${port} está ocupado. Cambia PORT en .env o detén la aplicación que lo está usando.`,
  EPERM:'Esta sesión no permite abrir puertos o conectarse a servicios locales. Ejecuta npm run local en una terminal del sistema fuera del sandbox.',
  EACCES:'Faltan permisos para abrir el puerto o conectarse al servicio. Usa una terminal con los permisos correspondientes.',
  ECONNREFUSED:`MySQL no responde en el puerto ${dbPort}. Inicia la base con npm run local o revisa DB_HOST y DB_PORT.`,
  ER_ACCESS_DENIED_ERROR:'MySQL rechazó la cuenta. Revisa DB_USER y DB_PASSWORD; un volumen existente conserva su contraseña original.',
  ER_BAD_DB_ERROR:'La base no está inicializada. Ejecuta npm run local para prepararla sin borrar datos.',
  ER_NO_SUCH_TABLE:'El esquema está incompleto. Revisa la inicialización; no elimines el volumen con datos.',
  ENOTFOUND:'No se pudo resolver DB_HOST. Usa db dentro de Docker y 127.0.0.1 para ejecutar Node en el host.',
  EAI_AGAIN:'No se pudo resolver DB_HOST. Revisa la red y el nombre del servidor de base de datos.'
 };
 return messages[error.code]||`No se pudo iniciar la aplicación (${error.code||'error de configuración'}). Revisa npm run doctor.`;
}
