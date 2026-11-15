# Complemento del diccionario de datos

El [diccionario físico original](DICCIONARIO.md) conserva tipos, longitudes, nulabilidad, valores predeterminados y las nueve FK. Para su lectura correcta:

- En Oferta, UNIQUE corresponde al **par** (id_solicitud, placa). Ninguno de los dos campos es único por separado.
- En Calificación, UNIQUE corresponde al **par** (id_viaje, id_usuario). Ninguno de los dos campos es único por separado.
- En Usuario, teléfono y correo son únicos por separado. En Conductor, usuario y licencia son únicos por separado. En Viaje y Pago son únicos id_oferta e id_viaje, respectivamente.
- Los valores y rangos permitidos, las dependencias funcionales y las reglas entre tablas se explican en [modelo lógico y normalización](MODELO-LOGICO-NORMALIZACION.md#dominios-y-reglas-principales). Los nombres y definiciones efectivos de las restricciones se encuentran en el [DDL](../database/01-schema.sql).
- El diccionario original refleja MariaDB 11.8.6; la fuente para MySQL es el DDL y, en ejecución, INFORMATION_SCHEMA. Solo hora_inicio y hora_fin permiten NULL de forma explícita.
