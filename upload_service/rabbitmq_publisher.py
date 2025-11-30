import pika
import json

def publish_uploaded_event(bucket: str, object_name: str):
    # Connect to RabbitMQ container
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host="rabbitmq")
    )

    channel = connection.channel()

    channel.queue_declare(queue="session_uploaded")

    message = {
        "bucket": bucket,
        "object_name": object_name
    }

    channel.basic_publish(
        exchange="",
        routing_key="session_uploaded",
        body=json.dumps(message)
    )

    print(f"[x] Sent event 'session_uploaded' with file {object_name}")

    connection.close()
