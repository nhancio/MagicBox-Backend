# Quick Start: Post Scheduling & WhatsApp Notifications

## 🚀 Quick Setup (5 minutes)

### 1. Install Redis
```bash
# Windows: Download from https://redis.io/download
# Or use WSL: wsl --install, then: sudo apt-get install redis-server

# Start Redis
redis-server
```

### 2. Configure Twilio (for WhatsApp)
Add to `.env`:
```env
TWILIO_ACCOUNT_SID=your_account_sid_here
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
```

**Get Twilio credentials:**
1. Sign up at https://www.twilio.com/ (free trial available)
2. Go to Console → Account → API Keys
3. Copy Account SID and Auth Token
4. Set up WhatsApp Sandbox (for testing) or get Business number

### 3. Start Celery Worker
```bash
cd backend
celery -A app.celery_app worker --loglevel=info
```

## 📝 Usage Examples

### Schedule a Post for Tomorrow Morning
```bash
POST /api/scheduling/schedule
Authorization: Bearer <token>

{
  "account_id": "your_social_account_id",
  "content": "Good morning! Here's today's update...",
  "scheduled_at": "2024-01-16T09:00:00Z",
  "notify_before_hours": 1,
  "user_phone": "+1234567890"
}
```

### Create Daily Morning Posts (Every Day at 9 AM)
```bash
POST /api/scheduling/recurring
Authorization: Bearer <token>

{
  "account_id": "your_social_account_id",
  "content": "Good morning! Check out our latest...",
  "start_date": "2024-01-16T00:00:00Z",
  "time_of_day": "09:00",
  "recurrence_pattern": "daily",
  "notify_before_hours": 1,
  "user_phone": "+1234567890"
}
```

## 🔔 What Happens

1. **Post Scheduled** → Saved in database with `SCHEDULED` status
2. **1 Hour Before** → WhatsApp notification sent automatically
3. **At Scheduled Time** → Post published automatically
4. **If Recurring** → Next occurrence created automatically

## ✅ Testing Without Celery

If Celery is not running:
- Posts are still saved in database
- Status remains `SCHEDULED`
- You can manually trigger publishing later
- Notifications won't be sent

## 📱 WhatsApp Notification Format

```
🔔 MagicBox Post Reminder

Your scheduled post is going live in 1 hour!

📝 Post: Good morning! Check out our latest...
📅 Time: 2024-01-16 09:00 UTC
🌐 Platform: Instagram

You can view or edit it in your MagicBox dashboard.
```

## 🎯 Common Use Cases

### Every Morning at 9 AM
```json
{
  "time_of_day": "09:00",
  "recurrence_pattern": "daily"
}
```

### Every Monday at 10 AM
```json
{
  "start_date": "2024-01-15T10:00:00Z",  // Next Monday
  "time_of_day": "10:00",
  "recurrence_pattern": "weekly"
}
```

### First of Every Month
```json
{
  "start_date": "2024-02-01T08:00:00Z",
  "time_of_day": "08:00",
  "recurrence_pattern": "monthly"
}
```

## 🔧 Troubleshooting

- **Posts not publishing**: Check Celery worker is running
- **Notifications not sending**: Verify Twilio credentials
- **Redis connection error**: Ensure Redis is running
- **Timezone issues**: All times are UTC
