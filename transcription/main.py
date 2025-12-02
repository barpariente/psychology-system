from rabbitmq_consumer import start_consumer

if __name__ == "__main__":
    print("Transcription service started. Waiting for 'audio_ready' events...")
    start_consumer()
