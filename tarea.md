# Tarea 8 - Buen Diseño: Cohesión y Acoplamiento

## Objetivo

La presente tarea tiene como objetivo que el estudiante diseñe e implemente una solución de software aplicando principios de buen diseño, arquitectura de software y calidad de código. La solución deberá evidenciar modularidad, abstracción, bajo acoplamiento y alta cohesión, considerando un escenario basado en mensajería y procesamiento de eventos.

* Diseñar una solución de software que soporte los atributos de modularidad, abstracción, bajo acoplamiento y alta cohesión.
* Implementar la solución utilizando un patrón arquitectónico adecuado, como Arquitectura Hexagonal, Clean Architecture, Microservicios o Arquitectura Orientada a Eventos.
* Modelar el sistema mediante un Diagrama de Casos de Uso, identificando actores, funcionalidades principales y relaciones relevantes.
* Incorporar un mecanismo de mensajería utilizando RabbitMQ, Apache Kafka o ActiveMQ, según el enfoque técnico elegido por el equipo.
* Aplicar buenas prácticas de calidad de software, incluyendo pruebas automatizadas, análisis estático de código y control de duplicidad.

---

## Introducción

Ir a un restaurante suele representar un gasto mayor que cocinar en casa; sin embargo, los programas de recompensas y fidelización permiten que los clientes obtengan beneficios por sus consumos. Estos programas ofrecen acumulación de puntos, reembolsos o beneficios especiales cada vez que un cliente consume en restaurantes afiliados.

Por ejemplo, Jesús desea ahorrar dinero para la educación de sus hijos. Cada vez que realiza una cena en un restaurante participante, una parte del consumo es transformada en puntos o recompensas que son abonadas a su cuenta personal.

Actualmente, debido a la necesidad de procesar grandes volúmenes de transacciones en tiempo real, las empresas utilizan arquitecturas orientadas a eventos y plataformas de mensajería como RabbitMQ, Apache Kafka o ActiveMQ, permitiendo desacoplar los sistemas y mejorar la escalabilidad, disponibilidad y resiliencia de las aplicaciones.

Implemente el proceso indicado en la Figura 1 considerando una arquitectura basada en mensajería y eventos:

* El restaurante registra la información de la cena realizada por el cliente.
* El sistema del restaurante procesa internamente la transacción y publica un mensaje en un Broker de Mensajería (RabbitMQ, Apache Kafka o ActiveMQ) con la siguiente información:

  * Monto consumido.
  * Número de tarjeta del cliente.
  * Código del restaurante afiliado.
  * Fecha y hora de la transacción.
* El Broker de Mensajería se encarga de la administración de colas, tópicos o eventos, garantizando la entrega de mensajes entre productores y consumidores.
* Un microservicio consumidor correspondiente al sistema de recompensas recibe el mensaje y calcula automáticamente los puntos, cashback o beneficios asociados al cliente.
* El sistema actualiza la cuenta de recompensas del cliente.
* Opcionalmente, el sistema puede publicar un nuevo evento para el envío de una notificación por correo electrónico, SMS o aplicación móvil indicando que la recompensa fue procesada exitosamente.

---

## Consideraciones Técnicas

El diseño debe considerar principios de:

* Alta cohesión.
* Bajo acoplamiento.
* Modularidad.
* Escalabilidad.
* Arquitectura orientada a eventos.

Asimismo, se recomienda aplicar algún patrón arquitectónico como:

* Arquitectura Hexagonal.
* Microservicios.
* Event-Driven Architecture (EDA).
* Clean Architecture.

---

# RabbitMQ

## Credenciales

| Parámetro    | Valor         |
| ------------ | ------------- |
| User         | students      |
| Password     | Ut3c2026      |
| Server       | 213.199.42.57 |
| Port         | 5672          |
| Virtual Host | /             |

## Ejemplo tipo vibecoded

### consumer-rabbit.py

```python
import pika
import sys
import os

credenciales = pika.PlainCredentials("students", "Ut3c2026")

parametros = pika.ConnectionParameters(
    "213.199.42.57",
    5672,
    "/",
    credenciales
)

def main():
    conexion = pika.BlockingConnection(parametros)
    canal = conexion.channel()

    # 2. Declarar la cola (por si el consumidor se ejecuta antes que el productor)
    nombre_cola = "laboratorio_1"

    canal.queue_declare(
        queue=nombre_cola,
        durable=True
    )

    # 3. Definir qué hacer cuando llega un mensaje
    def callback(ch, method, properties, body):
        print(f" [x] Mensaje recibido: {body.decode()}")

    # 4. Configurar el consumo de la cola
    canal.basic_consume(
        queue=nombre_cola,
        on_message_callback=callback,
        auto_ack=True
    )

    print(
        f' [*] Esperando mensajes en la cola "{nombre_cola}". '
        'Presiona CTRL+C para salir.'
    )

    canal.start_consuming()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n [*] Saliendo del consumidor...")
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
```

### producer-rabbit.py

```python
import pika

credenciales = pika.PlainCredentials("students", "Ut3c2026")

parametros = pika.ConnectionParameters(
    "213.199.42.57",
    5672,
    "/",
    credenciales
)

try:
    conexion = pika.BlockingConnection(parametros)

    canal = conexion.channel()

    # 2. Declarar la cola (crearla si no existe)
    nombre_cola = "laboratorio_1"

    canal.queue_declare(
        queue=nombre_cola,
        durable=True
    )

    # 3. Crear el mensaje y enviarlo
    mensaje = "¡Hola! Este es el primer mensaje del laboratorio."

    canal.basic_publish(
        exchange="",
        routing_key=nombre_cola,
        body=mensaje
    )

    print(f" [x] Mensaje enviado exitosamente: '{mensaje}'")

except Exception as e:
    print(f" [!] Error de conexión: {e}")

finally:
    # 4. Cerrar la conexión limpiamente
    if "conexion" in locals() and conexion.is_open:
        conexion.close()
```

---

# Apache Kafka

## Credenciales

| Parámetro | Valor         |
| --------- | ------------- |
| Server    | 213.199.42.57 |
| Port      | 9092          |

## Ejemplo tipo vibecoded

### consumer-kafka.py

```python
from confluent_kafka import Consumer

# 1. Configuración de conexión
configuracion = {
    "bootstrap.servers": "213.199.42.57:9092",
    "group.id": "grupo_estudiantes_1",
    "auto.offset.reset": "earliest",
}

# 2. Crear la instancia del Consumidor
consumidor = Consumer(configuracion)

tema = "laboratorio_1"

# 3. Suscribirse al tema
consumidor.subscribe([tema])

print(
    f" [*] Esperando mensajes en el topic '{tema}'. "
    "Presiona CTRL+C para salir."
)

try:
    # 4. Bucle infinito escuchando mensajes
    while True:

        # Pide mensajes al servidor
        msg = consumidor.poll(timeout=1.0)

        if msg is None:
            continue

        if msg.error():
            print(f" [!] Error de Kafka: {msg.error()}")
            continue

        texto = msg.value().decode("utf-8")
        print(f" [x] Mensaje recibido: {texto}")

except KeyboardInterrupt:
    print("\n [*] Deteniendo el consumidor...")

finally:
    # 5. Cerrar la conexión limpiamente
    consumidor.close()
```

### producer-kafka.py

```python
# Kafka solo crea el topic cuando el primer mensaje es enviado,
# por eso el productor se ejecuta antes que el consumidor

from confluent_kafka import Producer

# 1. Configuración de conexión
configuracion = {
    "bootstrap.servers": "213.199.42.57:9092"
}

# 2. Crear la instancia del Productor
productor = Producer(configuracion)

tema = "laboratorio_1"

# Función auxiliar para confirmar si el mensaje llegó o falló
def confirmacion_entrega(err, msg):
    if err is not None:
        print(f" [!] Error al entregar el mensaje: {err}")
    else:
        print(
            f" [x] Mensaje guardado en el topic "
            f"'{msg.topic()}' "
            f"(Partición: {msg.partition()})"
        )

# 3. Crear y enviar el mensaje
mensaje = "¡Hola Kafka! Este es el primer mensaje del laboratorio."

productor.produce(
    tema,
    value=mensaje.encode("utf-8"),
    callback=confirmacion_entrega
)

print(" [*] Enviando mensaje al servidor...")

# 4. Asegurarse de que el mensaje salga al servidor
productor.flush()
```

---

# SonarQube

## Credenciales

| Parámetro | Valor        |
| --------- | ------------ |
| User      | students     |
| Password  | Ut3c2026GG++ |

URL:

https://sonarqube.ingsoftware.lat/

## Requisitos

Deben tener instalado `sonar-scanner` y ejecutar:

```bash
sonar-scanner
```

Además, leer los comentarios incluidos en el archivo de configuración.

**Nota:** En caso los proyectos subidos a Sonar no estén listados de la forma que se indica en el archivo, no serán considerados para la evaluación.

---

## sonar-project.properties

```properties
# Poner las exclusiones de codigo que sean necesarias
# (Las mismas de un git ignore de python, ts, java, etc)

# Incluir la info de donde se ubican sus test
# y su archivo de cobertura

sonar.projectKey=Fabrizzio_Vilchez_t1

sonar.sources=.

sonar.exclusions=.venv/**, **/tests/**

sonar.host.url=https://sonarqube.ingsoftware.lat/

sonar.token=sqa_4e296de25b56b315988b9a9dfd137d2b4f97e7c3

# CONFIGURACIÓN DE PRUEBAS Y COBERTURA

sonar.tests=.

sonar.test.inclusions=**/tests/**, **test_*.py

sonar.python.coverage.reportPaths=coverage.xml
```

---

## Entregable

El proyecto deberá ser analizado mediante la plataforma SonarCloud con el objetivo de evaluar y mejorar la calidad del software desarrollado. El equipo deberá evidenciar buenas prácticas de ingeniería de software relacionadas con mantenibilidad, seguridad, confiabilidad y pruebas automatizadas.

El proyecto deberá alcanzar métricas vistas en clase en los siguientes atributos de calidad:

* Reliability (Confiabilidad).
* Security (Seguridad).
* Maintainability (Mantenibilidad).
* Duplications (Duplicación de código).

Asimismo, el sistema deberá alcanzar una cobertura mínima de pruebas (Test Coverage) del 85%.

Para evidenciar el cumplimiento de estas actividades, se deberá subir a Canvas lo siguiente:

* Enlace público del análisis realizado en SonarCloud (Coordinar con los ACL del curso).
* Enlace del repositorio del proyecto en GitHub.
* Evidencia de ejecución de pruebas automatizadas.
* Documento breve describiendo la arquitectura implementada y el patrón arquitectónico utilizado.
