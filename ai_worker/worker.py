# ai_worker/worker.py
import cv2
import pika
import json
import time
import os
import random
from datetime import datetime

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
RTSP_STREAM = os.getenv("RTSP_STREAM_URL", "rtsp://go2rtc:8554/test_cam")
MEDIA_DIR = "/app/media"

def connect_rabbitmq():
    """Connect to RabbitMQ with simple retry logic."""
    params = pika.URLParameters(RABBITMQ_URL)
    while True:
        try:
            connection = pika.BlockingConnection(params)
            print("Connected to RabbitMQ!")
            return connection
        except pika.exceptions.AMQPConnectionError:
            print("RabbitMQ not ready, retrying in 5 seconds...")
            time.sleep(5)

def main():
    # 1. Setup connection and queue
    connection = connect_rabbitmq()
    channel = connection.channel()
    channel.queue_declare(queue='ai_alerts', durable=True)

    # 2. Open Video Stream
    print(f"Connecting to RTSP stream: {RTSP_STREAM}")
    cap = cv2.VideoCapture(RTSP_STREAM)

    events = ["occupancy_detected", "spill_detected", "fire_hazard", "door_left_open"]

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame, retrying...")
            time.sleep(2)
            cap = cv2.VideoCapture(RTSP_STREAM) # Reconnect
            continue

        # We don't want to spam the broker, so we simulate processing time
        time.sleep(random.randint(3, 8)) 

        # Generate a mock event
        event_type = random.choice(events)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{event_type}_{timestamp}.jpg"
        filepath = os.path.join(MEDIA_DIR, filename)

        # Save the frame to the shared volume
        cv2.imwrite(filepath, frame)
        print(f"Saved snapshot to {filepath}")

        # Construct JSON payload
        payload = {
            "camera_id": "test_cam_01",
            "event_type": event_type,
            "confidence": round(random.uniform(0.75, 0.99), 2),
            "image_path": f"/media/{filename}"
        }

        # Publish to RabbitMQ
        channel.basic_publish(
            exchange='',
            routing_key='ai_alerts',
            body=json.dumps(payload),
            properties=pika.BasicProperties(delivery_mode=2) # Make message persistent
        )
        print(f"Published Alert: {payload}")

if __name__ == "__main__":
    main()