# backend/main.py
import os
import json
import threading
import pika
from fastapi import FastAPI
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://admin:password123@postgres:5432/facility_events")
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")

# Database Setup
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI(title="Facility Monitoring API")

def process_alert(ch, method, properties, body):
    """Callback function when a message is received from RabbitMQ."""
    alert_data = json.loads(body)
    print(f"Received Alert from RabbitMQ: {alert_data}")
    
    # Save to PostgreSQL
    db = SessionLocal()
    try:
        query = text("""
            INSERT INTO facility_events (camera_id, event_type, confidence, image_path) 
            VALUES (:camera_id, :event_type, :confidence, :image_path)
        """)
        db.execute(query, alert_data)
        db.commit()
        print("Alert saved to database successfully.")
    except Exception as e:
        db.rollback()
        print(f"Database error: {e}")
    finally:
        db.close()
        
    # Acknowledge the message so RabbitMQ removes it from the queue
    ch.basic_ack(delivery_tag=method.delivery_tag)

def start_rabbitmq_listener():
    """Runs in a background thread to listen to the message broker."""
    params = pika.URLParameters(RABBITMQ_URL)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    channel.queue_declare(queue='ai_alerts', durable=True)
    
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue='ai_alerts', on_message_callback=process_alert)
    
    print("RabbitMQ Listener started. Waiting for messages...")
    channel.start_consuming()

# Start the listener thread when FastAPI boots up
@app.on_event("startup")
def startup_event():
    listener_thread = threading.Thread(target=start_rabbitmq_listener, daemon=True)
    listener_thread.start()

# REST Endpoints
@app.get("/")
def read_root():
    return {"status": "Backend Engine Running"}

@app.get("/events")
def get_recent_events(limit: int = 10):
    """Fetch the latest events from the database."""
    db = SessionLocal()
    try:
        query = text("SELECT * FROM facility_events ORDER BY timestamp DESC LIMIT :limit")
        result = db.execute(query, {"limit": limit}).mappings().all()
        return {"events": result}
    finally:
        db.close()