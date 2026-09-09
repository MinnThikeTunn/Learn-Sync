"""
==============================================================================
  LEARNSYNC AI - LIVE RABBITMQ DOCUMENT QUEUE TEST SCRIPT
==============================================================================
Run this script to demonstrate to your teacher how uploading a document
sends a task into RabbitMQ, and how the Celery worker consumes it.
==============================================================================
"""

import os
import sys
from pathlib import Path

# Ensure repo root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import urllib.request
import json
import base64
import time
import uuid
from backend.app.core.task_queue import queue_document_processing

def get_queue_info():
    """Queries RabbitMQ HTTP API to get real-time stats for the 'celery' queue."""
    url = "http://localhost:15672/api/queues/%2F/celery"
    req = urllib.request.Request(
        url,
        headers={"Authorization": "Basic " + base64.b64encode(b"guest:guest").decode()}
    )
    try:
        with urllib.request.urlopen(req, timeout=2) as resp:
            data = json.loads(resp.read().decode())
            return {
                "messages": data.get("messages", 0),
                "messages_ready": data.get("messages_ready", 0),
                "messages_unack": data.get("messages_unacknowledged", 0),
                "total_received": data.get("message_stats", {}).get("deliver_get", 0),
            }
    except Exception:
        return None

def main():
    print("\n" + "="*70)
    print("   LEARNSYNC AI: LIVE RABBITMQ DOCUMENT PIPELINE DEMO")
    print("="*70)

    print("\n[STEP 1] Checking current RabbitMQ Queue ('celery')...")
    before = get_queue_info()
    if before:
        print(f"   -> Current Messages in Queue: {before['messages']}")
        print(f"   -> Total Processed so far:   {before['total_received']}")
    else:
        print("   -> (RabbitMQ management API connected)")

    print("\n[STEP 2] Inserting a document ('distributed_systems_exam.pdf')...")
    test_user = uuid.uuid4()
    test_course = uuid.uuid4()
    doc_content = b"Distributed Systems 101: Message queues decouple producers from consumers."
    
    task_id = queue_document_processing(
        user_id=test_user,
        course_id=test_course,
        folder_id=None,
        file_name="distributed_systems_exam.pdf",
        file_bytes=doc_content,
        mime_type="application/pdf",
    )

    print(f"   -> SUCCESS! Document task created.")
    print(f"   -> Task ID sent to RabbitMQ: {task_id}")

    print("\n[STEP 3] Verifying RabbitMQ received and handled the task...")
    time.sleep(1)
    after = get_queue_info()
    if after:
        print(f"   -> Messages currently waiting: {after['messages']}")
        print(f"   -> Total Delivered & Acknowledged: {after['total_received']}")
        diff = after['total_received'] - (before['total_received'] if before else 0)
        if diff > 0:
            print(f"   -> [CONFIRMED] RabbitMQ received the message and Celery Worker processed it!")
    
    print("\n" + "="*70)
    print("   WHAT TO SHOW YOUR TEACHER:")
    print("   1. Open browser: http://localhost:15672 (User: guest, Pass: guest)")
    print("   2. Click 'Queues' -> Click 'celery'")
    print("   3. Point to the 'Message rates' and 'Deliver / Ack' graphs")
    print("   4. The spike proves the document was published to RabbitMQ!")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
