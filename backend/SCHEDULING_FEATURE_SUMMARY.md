# Post Scheduling & WhatsApp Notifications - Feature Summary

## ✅ Implemented Features

### 1. Scheduled Posts
- **One-time scheduling**: Schedule posts for specific date/time
- **Recurring schedules**: Daily, weekly, or monthly recurring posts
- **Time-based**: Set specific time of day (e.g., 9:00 AM every morning)

### 2. WhatsApp Notifications
- **Pre-post notifications**: Sent 1 hour before scheduled post
- **Customizable timing**: Configurable hours before post (default: 1 hour)
- **Rich notifications**: Includes post preview, time, and platform info

### 3. Background Processing
- **Celery tasks**: Automated publishing and notifications
- **Redis broker**: Reliable task queue
- **Error handling**: Failed posts marked with error messages

## 📋 API Endpoints

### Schedule a Post
```bash
POST /api/scheduling/schedule
{
  "account_id": "social_account_uuid",
  "content": "Your post content",
  "scheduled_at": "2024-01-15T09:00:00Z",
  "notify_before_hours": 1,
  "user_phone": "+1234567890"
}
```

### Create Recurring Schedule (Every Morning)
```bash
POST /api/scheduling/recurring
{
  "account_id": "social_account_uuid",
  "content": "Good morning! Check out our latest update...",
  "start_date": "2024-01-15T00:00:00Z",
  "time_of_day": "09:00",
  "recurrence_pattern": "daily",
  "notify_before_hours": 1,
  "user_phone": "+1234567890"
}
```

### List Scheduled Posts
```bash
GET /api/scheduling/scheduled?account_id=<uuid>
```

### Cancel Scheduled Post
```bash
DELETE /api/scheduling/scheduled/{post_id}
```

## 🔧 Setup Instructions

### 1. Install Redis
```bash
# Windows: Download from https://redis.io/download
# Linux: sudo apt-get install redis-server
# Mac: brew install redis

# Start Redis
redis-server
```

### 2. Configure Twilio WhatsApp
Add to `.env`:
```env
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
```

### 3. Start Celery Worker
```bash
cd backend
celery -A app.celery_app worker --loglevel=info
```

## 📱 WhatsApp Notification Example

When a post is scheduled for 9:00 AM, user receives at 8:00 AM:

```
🔔 MagicBox Post Reminder

Your scheduled post is going live in 1 hour!

📝 Post: Good morning! Check out our latest...
📅 Time: 2024-01-15 09:00 UTC
🌐 Platform: Instagram

You can view or edit it in your MagicBox dashboard.
```

## 🔄 Workflow

1. **User schedules post** → API creates SocialPost with SCHEDULED status
2. **Celery tasks scheduled**:
   - Notification task: 1 hour before
   - Publishing task: At scheduled time
3. **Notification sent** → WhatsApp message 1 hour before
4. **Post published** → Automatically at scheduled time
5. **If recurring** → Next occurrence created automatically

## 🎯 Use Cases

### Daily Morning Posts
```json
{
  "time_of_day": "09:00",
  "recurrence_pattern": "daily",
  "content": "Good morning! Here's today's tip..."
}
```

### Weekly Updates
```json
{
  "time_of_day": "10:00",
  "recurrence_pattern": "weekly",
  "content": "Weekly roundup of our best content..."
}
```

### Monthly Reports
```json
{
  "time_of_day": "08:00",
  "recurrence_pattern": "monthly",
  "content": "Monthly performance report..."
}
```

## ⚠️ Important Notes

1. **Celery Required**: Background tasks require Celery worker running
2. **Redis Required**: Celery needs Redis as message broker
3. **Twilio Setup**: WhatsApp notifications require Twilio account
4. **Timezone**: All times are UTC (convert in frontend)
5. **Phone Format**: Accepts `+1234567890` or `1234567890` (auto-formats)

## 🚀 Production Considerations

1. **Use Celery Beat** for periodic task scheduling
2. **Monitor workers** for failures
3. **Add retry logic** for failed posts
4. **Store task IDs** for cancellation
5. **Use WhatsApp Business API** for production (not Sandbox)
6. **Database fallback** if Celery unavailable
