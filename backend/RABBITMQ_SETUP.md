# RabbitMQ Setup Guide for MagicBox

## Overview
MagicBox uses RabbitMQ as the message broker for Celery background tasks (scheduled posts and WhatsApp notifications).

## Installation

### Windows
1. Download Erlang from https://www.erlang.org/downloads
2. Download RabbitMQ from https://www.rabbitmq.com/download.html
3. Install both (Erlang first, then RabbitMQ)
4. RabbitMQ service should start automatically

### Linux
```bash
sudo apt-get update
sudo apt-get install rabbitmq-server
sudo systemctl enable rabbitmq-server
sudo systemctl start rabbitmq-server
```

### Mac
```bash
brew install rabbitmq
brew services start rabbitmq
```

## Configuration

### 1. Environment Variables (.env)
Add to your `.env` file:
```env
# RabbitMQ Configuration
CELERY_BROKER_URL=amqp://guest:guest@localhost:5672//
CELERY_RESULT_BACKEND=rpc://
```

**For Production:**
```env
CELERY_BROKER_URL=amqp://username:password@rabbitmq-host:5672/vhost
CELERY_RESULT_BACKEND=rpc://
```

### 2. RabbitMQ Management Plugin
Enable web management interface:
```bash
rabbitmq-plugins enable rabbitmq_management
```

Access at: http://localhost:15672
- Default username: `guest`
- Default password: `guest`

### 3. Create Custom User (Optional, Recommended for Production)
```bash
# Create user
rabbitmqctl add_user magicbox_user your_password

# Set permissions
rabbitmqctl set_permissions -p / magicbox_user ".*" ".*" ".*"

# Set as administrator
rabbitmqctl set_user_tags magicbox_user administrator
```

Then update `.env`:
```env
CELERY_BROKER_URL=amqp://magicbox_user:your_password@localhost:5672//
```

## Starting Services

### 1. Start RabbitMQ
```bash
# Windows (if service not running)
net start RabbitMQ

# Linux
sudo systemctl start rabbitmq-server

# Mac
brew services start rabbitmq

# Or manually
rabbitmq-server
```

### 2. Verify RabbitMQ is Running
```bash
rabbitmqctl status
```

Should show:
- Node: rabbit@hostname
- Status: running

### 3. Start Celery Worker
```bash
cd backend
celery -A app.celery_app worker --loglevel=info
```

### 4. Start Celery Beat (for periodic tasks)
```bash
celery -A app.celery_app beat --loglevel=info
```

## Testing Connection

### Test RabbitMQ Connection
```bash
# Check if RabbitMQ is accessible
rabbitmqctl ping
```

### Test Celery Connection
```python
from app.celery_app import celery_app
celery_app.control.inspect().active()
```

## Monitoring

### RabbitMQ Management UI
- URL: http://localhost:15672
- Username: `guest`
- Password: `guest`

**Features:**
- View queues
- Monitor message rates
- Check connections
- View exchanges and bindings

### Celery Monitoring
```bash
# List active tasks
celery -A app.celery_app inspect active

# List scheduled tasks
celery -A app.celery_app inspect scheduled

# List registered tasks
celery -A app.celery_app inspect registered
```

## Troubleshooting

### RabbitMQ Not Starting
```bash
# Check logs
rabbitmq-server -detached  # Start in background
rabbitmqctl status

# Reset if needed (WARNING: Deletes all data)
rabbitmqctl stop_app
rabbitmqctl reset
rabbitmqctl start_app
```

### Celery Can't Connect
1. Verify RabbitMQ is running: `rabbitmqctl status`
2. Check broker URL in `.env`
3. Verify credentials are correct
4. Check firewall/port 5672 is open

### Connection Refused
- Ensure RabbitMQ service is running
- Check port 5672 is not blocked
- Verify hostname in CELERY_BROKER_URL

## Production Considerations

1. **Use Virtual Hosts**: Create separate vhosts for different environments
2. **Strong Passwords**: Don't use default `guest/guest`
3. **SSL/TLS**: Enable for production
4. **Clustering**: Set up RabbitMQ cluster for HA
5. **Monitoring**: Use RabbitMQ management plugin
6. **Resource Limits**: Configure memory and disk limits

## Default Configuration

- **Host**: localhost
- **Port**: 5672 (AMQP), 15672 (Management)
- **Default User**: guest
- **Default Password**: guest
- **Virtual Host**: / (root)

## Queue Names

Celery automatically creates queues:
- `celery` - Default queue for tasks
- Task-specific queues as needed

## Next Steps

1. ✅ RabbitMQ installed and running
2. ✅ Environment variables configured
3. ✅ Celery worker started
4. ✅ Test scheduled post
5. ✅ Verify WhatsApp notification
