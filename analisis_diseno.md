# Documento de Análisis y Diseño
## Sistema de Recompensas para Restaurantes Afiliados

**Laboratorio 8 – Cohesión y Acoplamiento**  
**Curso:** CS3081 – Ingeniería de Software  
**Fecha:** 2026-05-31

---

## 1. Introducción

Los programas de fidelización en restaurantes permiten que los clientes acumulen puntos o cashback cada vez que consumen en locales afiliados. El presente sistema automatiza este flujo mediante una arquitectura orientada a eventos: el restaurante registra una cena, publica un evento en RabbitMQ y un servicio de recompensas independiente lo consume, calcula los beneficios y actualiza la cuenta del cliente.

El objetivo del diseño es que los dos servicios principales —el **Restaurant Service** y el **Rewards Service**— sean completamente autónomos y se comuniquen exclusivamente a través de mensajes asincrónicos, logrando bajo acoplamiento, alta cohesión y escalabilidad independiente.

**Alcance del sistema:**

- Registro de cenas de restaurantes afiliados vía REST.
- Publicación de eventos `cena.registrada` en RabbitMQ.
- Cálculo automático de puntos y cashback por el Rewards Service.
- Actualización de la cuenta de recompensas del cliente.
- Notificación opcional al cliente al acreditar la recompensa (`recompensa.procesada`).

---

## 2. Arquitectura

### 2.1 Patrón Arquitectónico

El sistema combina dos patrones complementarios:

**Event-Driven Architecture (EDA):** los servicios se comunican exclusivamente mediante eventos publicados en RabbitMQ. Ningún servicio llama directamente a otro. Esto garantiza desacoplamiento temporal y espacial.

**Arquitectura Hexagonal (Ports & Adapters) por servicio:** cada microservicio organiza su código en tres capas concéntricas:

```
┌─────────────────────────────────────────┐
│           Infrastructure Layer          │
│  (Adapters: AMQP, REST, SQLite)         │
│  ┌───────────────────────────────────┐  │
│  │        Application Layer          │  │
│  │  (Use Cases / Command Handlers)   │  │
│  │  ┌─────────────────────────────┐  │  │
│  │  │       Domain Layer          │  │  │
│  │  │  (Entities, Ports, Rules)   │  │  │
│  │  └─────────────────────────────┘  │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

- **Domain Layer:** entidades, objetos de valor y servicios de dominio. No depende de nada externo.
- **Application Layer:** casos de uso que orquestan la lógica de dominio. Depende solo del dominio y de los puertos (interfaces abstractas).
- **Infrastructure Layer:** adaptadores concretos (RabbitMQ, SQLite, FastAPI). Implementa los puertos definidos en el dominio.

---

### 2.2 Componentes

| Componente | Rol | Tecnología |
|---|---|---|
| **Restaurant Service** | Expone una API REST para registrar cenas y publica el evento `cena.registrada` al broker. Actúa como productor AMQP. | Python 3.12, FastAPI, Pika |
| **Rewards Service** | Consume eventos de cena, aplica reglas de negocio para calcular puntos/cashback, actualiza la cuenta del cliente y publica `recompensa.procesada`. | Python 3.12, FastAPI, Pika, SQLite |
| **Notifier** | Consume el evento `recompensa.procesada` y simula el envío de una notificación al cliente (log mock). Componente opcional dentro del Rewards Service. | Python 3.12, Pika |
| **RabbitMQ Broker** | Gestiona el exchange, las colas y el enrutamiento de mensajes entre productores y consumidores. | RabbitMQ (servidor compartido de la cátedra) |
| **shared/messaging** | Módulo compartido que contiene los contratos de eventos (`DinnerEvent`, `RewardProcessedEvent`), la topología AMQP, serialización JSON y helpers de seguridad. | Python puro |

**Diagrama de componentes:**

```
┌──────────────────┐   REST POST /dinners   ┌─────────────────────────┐
│  Cliente HTTP    │ ──────────────────────► │   Restaurant Service    │
│  (Restaurante)   │                         │  ┌───────────────────┐  │
└──────────────────┘                         │  │   Domain Layer    │  │
                                             │  │  (Dinner entity)  │  │
                                             │  └───────────────────┘  │
                                             │  ┌───────────────────┐  │
                                             │  │ Application Layer │  │
                                             │  │ RegisterDinner UC │  │
                                             │  └───────────────────┘  │
                                             │  ┌───────────────────┐  │
                                             │  │  Infra: FastAPI   │  │
                                             │  │  RabbitMQ Pub.    │  │
                                             └──┤───────────────────┤  │
                                                │  AMQP Publisher   │  │
                                                └────────┬──────────┘  │
                                                         │ cena.registrada
                                                         ▼
                                             ┌────────────────────────┐
                                             │       RabbitMQ         │
                                             │  Exchange: recompensas_exchange
                                             │  Queue: cenas_registradas
                                             │  Queue: notificaciones  │
                                             └───────────┬────────────┘
                                                         │ Consume
                                             ┌───────────▼────────────┐
                                             │    Rewards Service      │
                                             │  ┌───────────────────┐ │
                                             │  │   Domain Layer    │ │
                                             │  │ (Reward, Calc.)   │ │
                                             │  └───────────────────┘ │
                                             │  ┌───────────────────┐ │
                                             │  │ Application Layer │ │
                                             │  │ ProcessDinner UC  │ │
                                             │  └───────────────────┘ │
                                             │  ┌───────────────────┐ │
                                             │  │  SQLite DB        │ │
                                             │  │  FastAPI /rewards │ │
                                             │  │  RabbitMQ Pub.    │ │
                                             └──┴───────┬───────────┘ │
                                                        │ recompensa.procesada
                                             ┌──────────▼─────────────┐
                                             │       Notifier          │
                                             │  (log / email mock)     │
                                             └─────────────────────────┘
```

---

### 2.3 Topología AMQP

Se usa un único exchange de tipo **direct** con dos routing keys para separar los dos flujos de eventos.

#### Exchange único compartido

| Atributo | Valor |
|---|---|
| Nombre | `recompensas_exchange_Andre_Contreras_t1` |
| Tipo | `direct` |
| Durable | `true` |

#### Colas y routing keys

| Routing Key | Cola destino | Productor | Consumidor |
|---|---|---|---|
| `cena.registrada` | `cenas_registradas_Andre_Contreras_t1` | Restaurant Service | Rewards Service |
| `recompensa.procesada` | `notificaciones_Andre_Contreras_t1` | Rewards Service | Notifier |

#### Formato del mensaje `cena.registrada` (`DinnerEvent`)

```json
{
  "transaction_id": "uuid-v4",
  "amount": 85.50,
  "card_number": "4111111111111111",
  "restaurant_code": "REST-001",
  "timestamp": "2026-05-30T20:15:00Z"
}
```

#### Formato del mensaje `recompensa.procesada` (`RewardProcessedEvent`)

```json
{
  "transaction_id": "uuid-v4",
  "card_number": "4111111111111111",
  "points": 85,
  "cashback": 4.28,
  "restaurant_code": "REST-001",
  "timestamp": "2026-05-30T20:15:00Z"
}
```

#### Flujo completo de mensajes

```
Restaurant Service
      │
      │ basic_publish(exchange="recompensas_exchange_...",
      │               routing_key="cena.registrada",
      │               body=<DinnerEvent JSON>, delivery_mode=2)
      │
      ▼
RabbitMQ ──► cenas_registradas_...
                    │
                    │ basic_consume (prefetch_count=1)
                    ▼
            Rewards Service (ProcessDinner UC)
                    │
                    │ basic_publish(routing_key="recompensa.procesada")
                    ▼
RabbitMQ ──► notificaciones_...
                    │
                    ▼
                Notifier (log mock)
```

---

### 2.4 Decisiones de Refactoring Aplicadas

Durante la implementación se identificaron oportunidades de mejora sobre el código base original. Los cambios introducidos reducen la duplicación sin alterar la funcionalidad:

| Cambio | Archivo(s) afectado(s) | Problema resuelto |
|---|---|---|
| Nuevo `shared/messaging/rabbitmq_base.py` con `rabbitmq_channel`, `declare_exchange_queue_binding` y `RabbitMQPublisherMixin` | `rabbitmq_publisher.py`, `rabbitmq_notification_publisher.py`, `rabbitmq_consumer.py`, `notifier.py` | El patrón connect/declare/publish/close estaba copiado íntegramente en cuatro archivos (~40 líneas duplicadas). El mixin lo centraliza; cada adaptador queda en ~15 líneas. |
| `to_dict` usa `dataclasses.asdict(self)` y `from_dict` usa helper genérico `_from_dict` | `shared/messaging/events.py` | Eliminaba boilerplate de serialización por campo; evita que un campo nuevo se olvide en `to_dict`. |
| `build_connection_parameters` movida a `BrokerSettings.to_pika_parameters()` | `shared/messaging/topology.py` | La función libre creaba un segundo lugar donde mantener la lógica de conexión. Queda como alias de compatibilidad. |
| Context manager `db_connection(db_path)` | `rewards_service/infrastructure/database.py`, ambos repositorios SQLite | Cada método de los repositorios abría y cerraba la conexión manualmente con try/finally duplicado. El context manager elimina ese patrón. |

---

### 2.5 Atributos de Calidad

| Atributo | Cómo se atiende |
|---|---|
| **Bajo acoplamiento** | Los servicios no se importan entre sí. El único contrato compartido es el módulo `shared/messaging` (eventos + topología). El broker es el único intermediario en tiempo de ejecución. |
| **Alta cohesión** | Cada módulo tiene una sola razón de cambio. El `RewardCalculator` solo calcula; el `DinnerConsumer` solo orquesta ACK/NACK; los repositorios solo persisten. |
| **Modularidad** | La Arquitectura Hexagonal permite reemplazar SQLite por PostgreSQL, o RabbitMQ por Kafka, modificando solo los adaptadores de infraestructura sin tocar dominio ni aplicación. |
| **Escalabilidad** | Al ser asincrónicos y usar `prefetch_count=1`, se pueden ejecutar múltiples instancias del Rewards Service consumiendo la misma cola sin duplicar el procesamiento. |
| **Resiliencia** | Colas durables + mensajes persistentes (`delivery_mode=2`). Si el Rewards Service cae, los mensajes se acumulan y se procesan al reiniciarse. NACK con requeue en caso de error transitorio. |
| **Mantenibilidad** | Cobertura de pruebas ≥ 85% (obtenida: 98%). Análisis estático con SonarCloud. Los puertos (interfaces ABC) permiten testear la lógica de dominio con mocks sin infraestructura real. |

---

## 3. Reglas de Negocio

| ID | Regla |
|---|---|
| **RN-01** | Solo se procesan transacciones de restaurantes cuyo código esté registrado como afiliado y activo en el catálogo. |
| **RN-02** | El monto mínimo para acumular recompensas es **$10.00**. Transacciones por debajo de este umbral no generan puntos ni cashback. |
| **RN-03** | Se acredita **1 punto por cada $1.00** consumido (parte entera). Ejemplo: $85.50 → 85 puntos. |
| **RN-04** | El cashback varía según la categoría del restaurante: **premium** → 5% del monto; **estándar** → 2% del monto. |
| **RN-05** | Los restaurantes se clasifican en dos categorías: `premium` y `estandar`. |
| **RN-06** | Cada `transaction_id` se procesa **exactamente una vez** (idempotencia): si llega un ID ya procesado, el mensaje se descarta con ACK sin recalcular. |
| **RN-07** | El número de tarjeta debe tener entre 13 y 19 dígitos numéricos. |
| **RN-08** | El `restaurant_code` debe existir en el catálogo de afiliados; de lo contrario, el evento se descarta y se registra en log. |

---

## 4. Casos de Uso

### 4.1 Actores

| Actor | Tipo | Descripción |
|---|---|---|
| **Restaurante** | Primario (externo) | Sistema del restaurante afiliado que registra la cena vía API REST. |
| **Rewards Service** | Secundario (sistema) | Microservicio que procesa automáticamente los eventos de cena. |
| **Notifier** | Secundario (sistema) | Componente que simula notificación al cliente. |
| **Cliente** | Secundario (externo) | Persona cuya cuenta de recompensas se actualiza. |

### 4.2 Diagrama de Casos de Uso (UML textual)

```
+---------------------------------------------------------------------+
|              Sistema de Recompensas para Restaurantes               |
|                                                                     |
|  (Restaurante) ──► [CU-01 Registrar Cena]                           |
|                           │ <<include>>                             |
|                           ▼                                         |
|                   [CU-02 Publicar DinnerEvent]                      |
|                                                                     |
|  (Rewards Svc) ──► [CU-02 Procesar DinnerEvent]                     |
|                           │ <<include>>                             |
|                           ▼                                         |
|                   [CU-03 Calcular y Acreditar Recompensa]           |
|                           │ <<extend>>                              |
|                           ▼                                         |
|                   [CU-04 Notificar al Cliente] ◄── (Notifier)       |
|                                                                     |
|  (Cliente)     ──► [CU-05 Consultar Saldo]                          |
+---------------------------------------------------------------------+
```

### 4.3 Especificación de Casos de Uso

#### CU-01 – Registrar Cena

| Campo | Detalle |
|---|---|
| **Actor principal** | Restaurante |
| **Precondición** | — |
| **Postcondición** | La cena queda validada y se dispara CU-02. |

**Flujo principal:**
1. El restaurante envía `POST /dinners` con: `amount`, `card_number`, `restaurant_code`, `timestamp`.
2. El sistema valida `amount > 0`, `card_number` entre 13-19 dígitos, `restaurant_code` no vacío.
3. El sistema genera un `transaction_id` (UUID v4) y ejecuta CU-02.
4. Retorna `HTTP 202 Accepted` con `status` y `restaurant_code`.

**Flujo alternativo – Validación fallida:**
2a. Datos inválidos → `HTTP 400 Bad Request` con detalle del error.

**Flujo alternativo – Broker caído:**
3a. Error al publicar → `HTTP 503 Service Unavailable`.

---

#### CU-02 – Publicar DinnerEvent al Broker

| Campo | Detalle |
|---|---|
| **Actor principal** | Restaurant Service |
| **Relación** | `<<include>>` desde CU-01 |
| **Postcondición** | `DinnerEvent` JSON encolado en `cenas_registradas_...` con persistencia. |

**Flujo principal:**
1. Serializa el `DinnerEvent` a JSON UTF-8.
2. Publica en el exchange con `routing_key="cena.registrada"` y `delivery_mode=2`.

---

#### CU-03 – Procesar DinnerEvent y Acreditar Recompensa

| Campo | Detalle |
|---|---|
| **Actor principal** | Rewards Service |
| **Precondición** | Mensaje en `cenas_registradas_...` con `transaction_id` no procesado. |
| **Postcondición** | Cuenta del cliente actualizada. Se dispara CU-04. |

**Flujo principal:**
1. Deserializa el `DinnerEvent`.
2. Verifica idempotencia (`transaction_id` no existe en `processed_transactions`).
3. Busca el restaurante en el catálogo; verifica que esté activo.
4. Calcula `Reward`: `points = floor(amount)`, `cashback = amount * rate`.
5. Verifica que `reward.is_positive` (monto ≥ RN-02).
6. Persiste en `processed_transactions` y `accounts` (upsert atómico).
7. Publica `RewardProcessedEvent` (CU-04).
8. ACK del mensaje.

**Flujos alternativos:**
- `transaction_id` duplicado → ACK sin procesar.
- Restaurante no encontrado o inactivo → ACK sin procesar.
- `amount < 10` → reward no positivo → ACK sin procesar.
- Error de repositorio o publicación → NACK con requeue.

---

#### CU-04 – Notificar al Cliente

| Campo | Detalle |
|---|---|
| **Actor principal** | Notifier |
| **Relación** | `<<extend>>` desde CU-03 |
| **Postcondición** | Notificación registrada en log con número de tarjeta enmascarado. |

**Flujo principal:**
1. Deserializa `RewardProcessedEvent`.
2. Registra en log: `card=****1111: +85 points, +4.28 cashback`.
3. ACK del mensaje.

---

#### CU-05 – Consultar Saldo de Recompensas

| Campo | Detalle |
|---|---|
| **Actor principal** | Cliente |
| **Postcondición** | Se retorna el saldo acumulado. |

**Flujo principal:**
1. `GET /rewards/{card_number}`.
2. El sistema consulta `accounts` por `card_number`.
3. Retorna `HTTP 200` con `total_points` y `total_cashback`.

**Flujo alternativo:** tarjeta sin cuenta → `HTTP 404`.

---

## 5. Requerimientos Funcionales

| ID | Descripción |
|---|---|
| **RF-01** | El Restaurant Service expone `POST /dinners` con campos `amount`, `card_number`, `restaurant_code`, `timestamp`. |
| **RF-02** | El Restaurant Service valida las reglas de dominio antes de publicar (monto, formato de tarjeta, código no vacío). |
| **RF-03** | El Restaurant Service publica un `DinnerEvent` JSON en RabbitMQ por cada cena válida. |
| **RF-04** | El Rewards Service consume mensajes de `cenas_registradas_...` de forma continua. |
| **RF-05** | El Rewards Service verifica idempotencia por `transaction_id` antes de procesar. |
| **RF-06** | El Rewards Service calcula puntos (`floor(amount)`) y cashback según categoría del restaurante. |
| **RF-07** | El Rewards Service persiste el saldo acumulado por `card_number`. |
| **RF-08** | El Rewards Service expone `GET /rewards/{card_number}` que retorna `total_points` y `total_cashback`. |
| **RF-09** | El Rewards Service publica `RewardProcessedEvent` al acreditar recompensas. |
| **RF-10** | El Notifier consume mensajes de `notificaciones_...` y registra la notificación en log. |

---

## 6. Requerimientos No Funcionales

| ID | Categoría | Descripción | Métrica |
|---|---|---|---|
| **RNF-01** | Disponibilidad | Los mensajes no deben perderse ante reinicios del servicio. | Colas durables + `delivery_mode=2`. |
| **RNF-02** | Escalabilidad | Múltiples instancias del Rewards Service sin procesamiento duplicado. | `prefetch_count=1` + idempotencia por `transaction_id`. |
| **RNF-03** | Mantenibilidad | Calificación `A` en Reliability, Security y Maintainability en SonarCloud. | Cero issues bloqueantes. |
| **RNF-04** | Cobertura de pruebas | Cobertura de pruebas automatizadas ≥ 85%. | Obtenida: 98% con `pytest --cov`. |
| **RNF-05** | Duplicación | Código duplicado < 3%. | Reducido con `RabbitMQPublisherMixin` y `db_connection`. |
| **RNF-06** | Seguridad | Credenciales nunca hardcodeadas; números de tarjeta enmascarados en logs. | Variables de entorno + `mask_card_number()`. |
| **RNF-07** | Bajo acoplamiento | Sin imports cruzados entre `restaurant_service` y `rewards_service`. | Verificable por análisis de imports. |

---

## 7. Modelos de Datos

El Rewards Service persiste en SQLite con tres tablas:

#### `restaurants` (catálogo seed)

| Campo | Tipo | Descripción |
|---|---|---|
| `code` | TEXT PK | Código único del restaurante |
| `name` | TEXT | Nombre del restaurante |
| `category` | TEXT | `premium` o `estandar` |
| `active` | INTEGER | 1 = activo, 0 = inactivo |

#### `accounts` (saldo acumulado por cliente)

| Campo | Tipo | Descripción |
|---|---|---|
| `card_number` | TEXT PK | Número de tarjeta del cliente |
| `total_points` | INTEGER | Puntos acumulados totales |
| `total_cashback` | REAL | Cashback acumulado total |

#### `processed_transactions` (registro de idempotencia)

| Campo | Tipo | Descripción |
|---|---|---|
| `transaction_id` | TEXT PK | UUID de la transacción ya procesada |
| `card_number` | TEXT | Tarjeta asociada |
| `processed_at` | TEXT | Timestamp de procesamiento |

---

## 8. Estrategia de Pruebas

### 8.1 Niveles de Prueba

| Nivel | Alcance | Herramienta |
|---|---|---|
| **Unitarias** | Dominio y casos de uso con todos los puertos mockeados | `pytest` + `unittest.mock` |
| **Integración** | Adaptadores SQLite con archivo temporal real; adaptadores RabbitMQ con `MagicMock` de pika | `pytest` + `tempfile` |

### 8.2 Casos de Prueba Clave

| ID | Tipo | Descripción |
|---|---|---|
| TP-01 | Unitaria | `amount=100`, restaurante premium → 100 puntos, $5.00 cashback. |
| TP-02 | Unitaria | `amount=85.75` → 85 puntos (parte entera). |
| TP-03 | Unitaria | `amount=9.99` → `reward.is_positive = False` → no se acredita. |
| TP-04 | Unitaria | `transaction_id` ya procesado → `ProcessDinner` retorna `None`, sin llamar a `add_reward`. |
| TP-05 | Unitaria | Restaurante inactivo → `ProcessDinner` retorna `None`. |
| TP-06 | Unitaria | `card_number` con menos de 13 dígitos → `DinnerValidationError`. |
| TP-07 | Unitaria | Error AMQP en publisher → `PublishError` propagado. |
| TP-08 | Integración | `add_reward` persiste en SQLite; `get_balance` retorna el saldo correcto. |
| TP-09 | Integración | Dos `add_reward` al mismo `card_number` acumulan correctamente. |
| TP-10 | Integración | `is_transaction_processed` retorna `True` tras un `add_reward`. |

### 8.3 Configuración de Cobertura

```ini
# pytest.ini
[pytest]
addopts = --cov=. --cov-report=xml:coverage.xml --cov-report=term-missing
testpaths = tests

[coverage:run]
omit =
    */main.py
    tests/*
    .venv/*
```

---

## 9. Estructura del Proyecto

```
laboratorio8/
├── restaurant_service/           # Productor AMQP
│   ├── domain/
│   │   └── dinner.py             # Entidad Dinner + validaciones
│   ├── application/
│   │   ├── ports.py              # Puerto DinnerEventPublisher
│   │   └── register_dinner.py   # CU-01: RegisterDinner
│   └── infrastructure/
│       ├── api.py                # Adaptador FastAPI
│       └── rabbitmq_publisher.py # Adaptador RabbitMQ (usa RabbitMQPublisherMixin)
│
├── rewards_service/              # Consumidor AMQP
│   ├── domain/
│   │   ├── restaurant.py         # Entidad Restaurant
│   │   ├── reward.py             # Value Object Reward
│   │   └── reward_calculator.py  # Servicio de dominio
│   ├── application/
│   │   ├── ports.py              # Puertos: AccountRepository, RestaurantRepository, NotificationPublisher
│   │   └── process_dinner.py    # CU-03: ProcessDinner
│   └── infrastructure/
│       ├── api.py                # Adaptador FastAPI (GET /rewards)
│       ├── database.py           # Schema SQLite + db_connection context manager
│       ├── sqlite_account_repository.py
│       ├── sqlite_restaurant_repository.py
│       ├── rabbitmq_consumer.py  # DinnerConsumer (on_message + start)
│       ├── rabbitmq_notification_publisher.py  # Usa RabbitMQPublisherMixin
│       └── notifier.py           # CU-04: Notifier (on_message + start)
│
├── shared/messaging/             # Contrato compartido (sin lógica de negocio)
│   ├── events.py                 # DinnerEvent, RewardProcessedEvent
│   ├── topology.py               # Nombres AMQP + BrokerSettings
│   ├── serialization.py          # serialize / deserialize JSON
│   ├── security.py               # mask_card_number
│   └── rabbitmq_base.py          # rabbitmq_channel, declare_exchange_queue_binding, RabbitMQPublisherMixin
│
└── tests/                        # Espejo de la estructura de código
    ├── restaurant_service/
    ├── rewards_service/
    └── shared/
```

---

## 10. Decisiones de Diseño

| ID | Decisión | Alternativa considerada | Razón |
|---|---|---|---|
| **DD-01** | **RabbitMQ** como broker. | Kafka, ActiveMQ. | Es el broker indicado por la cátedra. Adecuado para el volumen del laboratorio; API AMQP simple con `pika`. |
| **DD-02** | **Exchange único `direct`** con dos routing keys. | Dos exchanges separados. | Un exchange direct es suficiente y más simple de operar. Las routing keys `cena.registrada` y `recompensa.procesada` enrutan sin ambigüedad. |
| **DD-03** | **Arquitectura Hexagonal** por servicio. | Estructura plana por capas. | Permite testear dominio y aplicación sin infraestructura real. Los puertos (ABC) son el contrato; los adaptadores son reemplazables. |
| **DD-04** | **Manual acknowledgment** (`auto_ack=False`). | `auto_ack=True`. | El mensaje solo se elimina de la cola si fue procesado exitosamente. Errores transitorios hacen NACK con requeue. |
| **DD-05** | **SQLite** como base de datos. | PostgreSQL. | Simplifica el entorno de pruebas (sin servidor externo). Los repositorios implementan puertos abstractos, por lo que migrar a PostgreSQL solo requiere un nuevo adaptador. |
| **DD-06** | **UUID v4** como `transaction_id`. | Hash del contenido. | Generado por el Restaurant Service, es parte del contrato del mensaje y fácil de rastrear en logs. |
| **DD-07** | **`prefetch_count=1`** en el consumidor. | Sin prefetch. | Garantiza procesamiento justo entre múltiples instancias del Rewards Service corriendo en paralelo. |
| **DD-08** | **Variables de entorno** para credenciales. | Hardcoded en código. | Cumple RNF-06. `BrokerSettings.from_env()` lee `RABBITMQ_HOST`, `RABBITMQ_USER`, `RABBITMQ_PASSWORD`, etc. |
| **DD-09** | **`RabbitMQPublisherMixin`** para eliminar duplicación. | Copiar el patrón en cada publisher. | Los dos publishers tenían ~40 líneas idénticas. El mixin centraliza la lógica en un único lugar y expone un método `_do_publish` parametrizable. |
| **DD-10** | **`db_connection` context manager** para SQLite. | try/finally manual en cada método. | Elimina el patrón de apertura/cierre de conexión repetido en seis métodos de los dos repositorios. |
