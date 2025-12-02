import pika
import json
from transcription import process_video_file

def callback(ch, method, properties, body):
    message = json.loads(body)
    bucket = message["bucket"]
    video_name = message["object_name"]

    print(f"[x] Received analyzer event for file: {video_name}")

    process_video_file(bucket, video_name)

def start_consumer():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host="rabbitmq")
    )
    channel = connection.channel()

    channel.queue_declare(queue="analyzer")

    channel.basic_consume(
        queue="analyzer",
        on_message_callback=callback,
        auto_ack=True
    )

    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()
