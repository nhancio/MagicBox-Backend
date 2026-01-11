"""
Test script to verify RabbitMQ and Celery configuration.
"""
import sys
import os
sys.path.insert(0, 'src')

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    os.system('chcp 65001 >nul 2>&1')

from app.celery_app import celery_app
from app.config.settings import settings

print("=" * 60)
print("RabbitMQ & Celery Configuration Test")
print("=" * 60)

print(f"\n1. Settings Configuration:")
print(f"   CELERY_BROKER_URL: {settings.CELERY_BROKER_URL}")
print(f"   CELERY_RESULT_BACKEND: {settings.CELERY_RESULT_BACKEND}")

print(f"\n2. Celery App Configuration:")
print(f"   Broker: {celery_app.conf.broker_url}")
print(f"   Backend: {celery_app.conf.result_backend}")

print(f"\n3. Testing Connection...")
try:
    # Try to inspect active workers
    inspect = celery_app.control.inspect()
    active = inspect.active()
    
    if active:
        print(f"   [OK] Connected! Found {len(active)} active worker(s)")
        for worker, tasks in active.items():
            print(f"      Worker: {worker}")
            print(f"      Active tasks: {len(tasks)}")
    else:
        print(f"   [WARNING] Connected but no active workers")
        print(f"   [TIP] Start worker with: celery -A app.celery_app worker --loglevel=info")
        
except Exception as e:
    print(f"   [ERROR] Connection failed: {e}")
    print(f"   [TIP] Make sure RabbitMQ is running")
    print(f"   [TIP] Windows: Check Services or run: net start RabbitMQ")

print(f"\n4. Registered Tasks:")
try:
    inspect = celery_app.control.inspect()
    registered = inspect.registered()
    if registered:
        for worker, tasks in registered.items():
            print(f"   Worker: {worker}")
            for task in tasks:
                print(f"      - {task}")
    else:
        print(f"   No workers registered")
        print(f"   [TIP] Start worker to see registered tasks")
except Exception as e:
    print(f"   Could not get registered tasks: {e}")

print(f"\n5. Test Task Execution:")
try:
    # Test a simple task
    from app.tasks.publishing_tasks import publish_scheduled_post
    from app.tasks.notification_tasks import send_pre_post_notification
    print(f"   [OK] Tasks imported successfully")
    print(f"      - publish_scheduled_post")
    print(f"      - send_pre_post_notification")
except Exception as e:
    print(f"   [ERROR] Task import failed: {e}")

print("\n" + "=" * 60)
print("Test Complete!")
print("=" * 60)
print("\nNext Steps:")
print("1. Make sure RabbitMQ is running")
print("2. Add CELERY_BROKER_URL to .env file")
print("3. Start Celery worker: celery -A app.celery_app worker --loglevel=info")
