# Post Scheduling & WhatsApp Notifications Setup

## Overview
MagicBox now supports scheduled posts with WhatsApp notifications sent 1 hour before publishing.

## Features

1. **One-time Scheduled Posts**: Schedule a post for a specific date/time
2. **Recurring Schedules**: Daily, weekly, or monthly recurring posts (e.g., every morning at 9 AM)
3. **WhatsApp Notifications**: Automatic notification 1 hour before each scheduled post
4. **Flexible Notification Timing**: Configurable hours before post (default: 1 hour)

## Setup Requirements

### 1. Redis (for Celery)
```bash
# Install Redis
# Windows: Download from https://redis.io/download
# Linux/Mac: 
sudo apt-get install redis-server  # Ubuntu/Debian
brew install redis  # Mac

# Start Redis
redis-server
```

### 2. Twilio WhatsApp API
1. Sign up at https://www.twilio.com/
2. Get your Account SID and Auth Token
3. Set up WhatsApp Sandbox or get a WhatsApp Business number
4. Add to `.env`:
```env
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886  # Your Twilio WhatsApp number
```

### 3. Celery Worker
```bash
# Install dependencies
pip install celery redis twilio

# Start Celery worker (in separate terminal)
cd backend
celery -A app.celery_app worker --loglevel=info

# For production, use:
celery -A app.celery_app worker --loglevel=info --concurrency=4
```

### 4. Celery Beat (for periodic tasks - optional)
```bash
# Start Celery Beat scheduler
celery -A app.celery_app beat --loglevel=info
```

## API Endpoints

### Schedule a Post
```bash
POST /api/scheduling/schedule
Authorization: Bearer <token>

{
  "account_id": "social_account_uuid",
  "content": "Your post content here",
  "scheduled_at": "2024-01-15T09:00:00Z",
  "media_urls": ["https://example.com/image.jpg"],
  "notify_before_hours": 1,
  "user_phone": "+1234567890"
}
```

### Create Recurring Schedule
```bash
POST /api/scheduling/recurring
Authorization: Bearer <token>

{
  "account_id": "social_account_uuid",
  "content": "Daily morning post",
  "start_date": "2024-01-15T00:00:00Z",
  "time_of_day": "09:00",
  "recurrence_pattern": "daily",
  "recurrence_end_date": "2024-12-31T23:59:59Z",
  "notify_before_hours": 1,
  "user_phone": "+1234567890"
}
```

### List Scheduled Posts
```bash
GET /api/scheduling/scheduled?account_id=<uuid>&start_date=<date>&end_date=<date>
Authorization: Bearer <token>
```

### Cancel Scheduled Post
```bash
DELETE /api/scheduling/scheduled/{post_id}
Authorization: Bearer <token>
```

## Workflow

1. **User schedules a post** via API
2. **System creates** SocialPost with `SCHEDULED` status
3. **Celery tasks are scheduled**:
   - Notification task: 1 hour before post time
   - Publishing task: At post time
4. **Notification sent** via WhatsApp 1 hour before
5. **Post published** automatically at scheduled time
6. **If recurring**, next occurrence is created automatically

## WhatsApp Notification Format

```
🔔 MagicBox Post Reminder

Your scheduled post is going live in 1 hour!

📝 Post: [Post preview...]
📅 Time: 2024-01-15 09:00 UTC
🌐 Platform: Instagram

You can view or edit it in your MagicBox dashboard.
```

## Phone Number Format

- Accepts: `+1234567890`, `1234567890`, `whatsapp:+1234567890`
- Automatically formats to: `whatsapp:+1234567890`
- Defaults to US country code (+1) if not provided

## Error Handling

- If Celery is not running, posts are still saved but won't auto-publish
- If WhatsApp fails, post still publishes (notification is optional)
- Failed posts are marked with `FAILED` status and error message
- Retry logic can be added for failed posts

## Production Considerations

1. **Use Redis Cluster** for high availability
2. **Monitor Celery workers** for failures
3. **Set up alerts** for failed posts
4. **Use WhatsApp Business API** instead of Sandbox for production
5. **Add retry logic** for failed notifications
6. **Store task IDs** in database for cancellation
7. **Use database-based scheduler** as fallback if Celery unavailable

## Testing

1. **Test without Celery**: Posts are saved but won't auto-publish
2. **Test with Celery**: Start worker and schedule a test post
3. **Test WhatsApp**: Use Twilio Sandbox for testing
4. **Test Recurring**: Create daily schedule and verify next occurrences

## Troubleshooting

- **Posts not publishing**: Check Celery worker is running
- **Notifications not sending**: Verify Twilio credentials
- **Recurring not working**: Check recurrence pattern and end date
- **Timezone issues**: All times are UTC, convert in frontend
