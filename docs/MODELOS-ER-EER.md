# Modelo entidad-relación y especialización EER

Fuente de verdad: [esquema SQL](../database/01-schema.sql). La notación indica cero, uno o muchos en cada extremo. PK identifica; FK referencia. El diagrama lógico no sustituye los CHECK ni los triggers.

```mermaid
erDiagram
    USUARIO ||--o| CONDUCTOR : "puede ser"
    CONDUCTOR ||--o{ VEHICULO : posee
    USUARIO ||--o{ SOLICITUD : solicita
    SOLICITUD ||--o{ OFERTA : recibe
    VEHICULO ||--o{ OFERTA : presenta
    OFERTA ||--o| VIAJE : origina
    VIAJE ||--o| PAGO : registra
    VIAJE ||--o{ CALIFICACION : recibe
    USUARIO ||--o{ CALIFICACION : emite
    USUARIO {
        int id_usuario PK
        varchar nombres
        varchar telefono UK
        varchar correo UK
        datetime fecha_registro
    }
    CONDUCTOR {
        int id_conductor PK
        int id_usuario FK,UK
        varchar licencia UK
    }
    VEHICULO {
        varchar placa PK
        int id_conductor FK
        varchar marca
        varchar modelo
        varchar color
        smallint anio
    }
    SOLICITUD {
        int id_solicitud PK
        int id_usuario FK
        varchar origen
        varchar destino
        decimal precio_ofrecido
        varchar estado
        datetime fecha_solicitud
    }
    OFERTA {
        int id_oferta PK
        int id_solicitud FK
        varchar placa FK
        decimal monto
        smallint tiempo_llegada
    }
    VIAJE {
        int id_viaje PK
        int id_oferta FK,UK
        varchar estado
        datetime hora_inicio
        datetime hora_fin
    }
    PAGO {
        int id_pago PK
        int id_viaje FK,UK
        varchar metodo
        decimal monto
        decimal comision
        datetime fecha_pago
    }
    CALIFICACION {
        int id_calificacion PK
        int id_viaje FK
        int id_usuario FK
        tinyint puntaje
        varchar comentario
    }
```

Los pares (id_solicitud, placa) y (id_viaje, id_usuario) son únicos **en conjunto**, no por separado. Una oferta pertenece a una solicitud y vehículo; una solicitud y un vehículo pueden participar en muchas ofertas. Un viaje admite como máximo dos calificaciones por las reglas de participante y unicidad, aunque la FK aislada solo expresa 0..N. La aceptación de como máximo una oferta por solicitud depende del bloqueo y los triggers, no solo de la unicidad de id_oferta.

## EER: perfil de conductor

```mermaid
flowchart TD
    U["USUARIO<br/>id_usuario, nombres, teléfono, correo"] --> S{"Especialización parcial"}
    S --> C["CONDUCTOR<br/>licencia"]
    U --> P["Rol pasajero<br/>cuando crea una solicitud"]
    C -. "FK id_usuario UNIQUE y NOT NULL" .-> U
```

La especialización es **parcial**: puede haber usuarios sin perfil de conductor. Cada conductor corresponde a exactamente un usuario, y un usuario tiene como máximo un perfil de conductor. Pasajero es un rol en Solicitud, no otro subtipo implementado; un conductor también puede solicitar viajes. Al haber un solo subtipo representado, no corresponde imponer una disyunción entre subtipos ni inventar una especialización total. El esquema conserva id_conductor como PK y usa id_usuario como FK única para implementar la especialización.
