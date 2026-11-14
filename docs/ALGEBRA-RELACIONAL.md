# Álgebra relacional y SQL

Las expresiones omiten orden y LIMIT: el álgebra relacional trabaja con conjuntos; SQL puede conservar duplicados. En estos ejemplos la PK proyectada evita duplicados de filas distintas. Fuente: [consultas 3 y 4](../database/03-consultas.sql#L10-L14). Se usa ρ para renombrar, σ selección, π proyección y ⋈ reunión.

## 1. Solicitudes abiertas sin ofertas

La consulta SQL usa LEFT JOIN y filtra los valores sin correspondencia. Su expresión básica equivalente usa diferencia:

A = π_{id_solicitud}(σ_{estado='abierta'}(SOLICITUD))

B = π_{id_solicitud}(OFERTA)

Resultado = π_{id_solicitud,nombres,origen,destino,precio_ofrecido}((σ_{estado='abierta'}(SOLICITUD) ⋈_{SOLICITUD.id_usuario=USUARIO.id_usuario} USUARIO) ⋈_{SOLICITUD.id_solicitud=A.id_solicitud} ρ_A(A − B))

A y B tienen el mismo esquema y dominio, por lo que pueden restarse. El resultado contiene una fila por solicitud abierta sin oferta; nombres proviene del usuario.

## 2. Viajes y participantes

Basada en la primera consulta de [03-consultas.sql](../database/03-consultas.sql#L3-L4). Sean P=ρ_P(USUARIO), C=ρ_C(USUARIO), D=CONDUCTOR, A=VEHICULO, O=OFERTA, S=SOLICITUD y V=VIAJE:

R = V ⋈_{V.id_oferta=O.id_oferta} O
  ⋈_{O.id_solicitud=S.id_solicitud} S
  ⋈_{S.id_usuario=P.id_usuario} P
  ⋈_{O.placa=A.placa} A
  ⋈_{A.id_conductor=D.id_conductor} D
  ⋈_{D.id_usuario=C.id_usuario} C

Resultado = π_{V.id_viaje,P.nombres,C.nombres,S.origen,S.destino,O.placa,O.monto,V.estado,V.hora_inicio,V.hora_fin}(R)

Se renombra Usuario dos veces para diferenciar pasajero y conductor. En SQL, los alias también distinguen las dos columnas de nombre. El monto final se obtiene de Oferta; no se guarda de nuevo en Viaje. El orden descendente y LIMIT 200 pertenecen a la presentación SQL y no al álgebra básica.
