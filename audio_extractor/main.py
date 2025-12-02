from rabbitmq_consumer import start_consumer

if __name__ == "__main__":
    print("Audio Extractor service started. Listening for messages...")
    start_consumer()
