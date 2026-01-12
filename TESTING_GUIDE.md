# Testing Guide - Conversational Marketing Content Generation

## Overview
This guide helps you test the new conversational agent system for generating marketing content (images, posts, reels/shorts).

## Prerequisites
1. **Database Migration**: Run the migration to add `agent_id` to conversations table
   ```bash
   cd backend
   alembic upgrade head
   ```

2. **Environment Variables**: Ensure `GEMINI_API_KEY` is set in `.env`
   ```bash
   GEMINI_API_KEY=your_api_key_here
   ```

3. **Start Backend Server**:
   ```bash
   cd backend
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

## Test Endpoints

### 1. Test Image Generation (Quick Test)
**Endpoint**: `POST /api/test/image`

**Request**:
```json
{
  "prompt": "A vibrant coffee shop promotion image with warm colors and inviting atmosphere"
}
```

**Expected Response**:
```json
{
  "success": true,
  "image_path": "/path/to/generated/image.png",
  "prompt": "...",
  "metadata": {
    "model": "gemini-2.5-flash-image"
  }
}
```

### 2. Test Post Generation (Quick Test)
**Endpoint**: `POST /api/test/post`

**Request**:
```json
{
  "topic": "New product launch for small business",
  "tone": "professional",
  "platform": "instagram"
}
```

**Expected Response**:
```json
{
  "success": true,
  "content": "Generated post content...",
  "hashtags": ["#marketing", "#smallbusiness"],
  "caption": "...",
  "key_points": [...],
  "platform": "instagram"
}
```

### 3. Test Reel Generation (Quick Test)
**Endpoint**: `POST /api/test/reel`

**Request**:
```json
{
  "topic": "Product demonstration for marketing",
  "duration_seconds": 30,
  "generate_video": false
}
```

**Expected Response**:
```json
{
  "success": true,
  "script": "Generated reel script...",
  "hook": "Attention-grabbing hook...",
  "scenes": [...],
  "call_to_action": "..."
}
```

## Conversational Agent Testing

### 1. List Available Agents
**Endpoint**: `GET /api/projects/{project_id}/agents`

**Response**: List of available agents including:
- `image_agent` or `image_chat_agent`
- `reel_agent` or `reel_chat_agent`

### 2. Start Chat with Image Agent
**Endpoint**: `POST /api/projects/{project_id}/agents/{agent_id}/chat/message`

**Request**:
```json
{
  "message": "Create an image for my coffee shop promotion",
  "conversation_id": null
}
```

**Expected Response**:
```json
{
  "success": true,
  "response": "I've created a marketing image for you! ...",
  "conversation_id": "uuid-here",
  "message_id": "uuid-here",
  "artifact_id": "uuid-here",
  "metadata": {
    "image_path": "/path/to/image.png",
    "prompt": "...",
    "intent": {...}
  }
}
```

### 3. Continue Conversation
Use the same endpoint with the `conversation_id` from previous response:

**Request**:
```json
{
  "message": "Make it more vibrant",
  "conversation_id": "uuid-from-previous-response"
}
```

### 4. Start Chat with Reel Agent
**Endpoint**: `POST /api/projects/{project_id}/agents/{agent_id}/chat/message`

**Request**:
```json
{
  "message": "Create a reel for my product launch",
  "conversation_id": null
}
```

**Expected Response**:
```json
{
  "success": true,
  "response": "I've created a reel script for you! ...",
  "conversation_id": "uuid-here",
  "artifact_id": "uuid-here",
  "metadata": {
    "script": {...},
    "intent": {...}
  }
}
```

### 5. Get Conversation History
**Endpoint**: `GET /api/projects/{project_id}/agents/{agent_id}/chat/conversations/{conversation_id}/messages`

**Response**: List of all messages in the conversation

### 6. List All Conversations for Agent
**Endpoint**: `GET /api/projects/{project_id}/agents/{agent_id}/chat/conversations`

**Response**: List of all conversations with this agent

## Scheduling Generated Content

### 1. Schedule an Artifact (Generated Content)
**Endpoint**: `POST /api/projects/{project_id}/scheduling/schedule`

**Request**:
```json
{
  "account_id": "social_account_id",
  "artifact_id": "artifact_id_from_chat_response",
  "scheduled_at": "2026-01-15T10:00:00Z",
  "notify_before_hours": 1,
  "user_phone": "+1234567890"
}
```

**Expected Response**:
```json
{
  "success": true,
  "post_id": "uuid-here",
  "scheduled_at": "2026-01-15T10:00:00Z",
  "status": "SCHEDULED",
  "notification_scheduled": true
}
```

### 2. List Scheduled Posts
**Endpoint**: `GET /api/projects/{project_id}/scheduling/scheduled`

**Response**: List of all scheduled posts with status, content, and timing

### 3. Cancel Scheduled Post
**Endpoint**: `DELETE /api/projects/{project_id}/scheduling/scheduled/{post_id}`

## Testing Flow

### Complete Workflow Test:

1. **Create/Login** → Get project_id
2. **List Agents** → Get agent_id for image_agent and reel_agent
3. **Chat with Image Agent**:
   - Send: "Create an Instagram post image for my coffee shop"
   - Get artifact_id from response
   - Continue: "Make it more colorful"
4. **Chat with Reel Agent**:
   - Send: "Create a 30-second reel about our new product"
   - Get artifact_id from response
5. **Schedule Content**:
   - Schedule the image artifact for tomorrow at 10 AM
   - Schedule the reel artifact for next week
6. **Verify Scheduling**:
   - List scheduled posts
   - Verify they appear correctly

## Expected Behavior

### Image Agent:
- Understands natural language requests
- Generates marketing images using Gemini 2.5 Flash Image
- Maintains conversation context
- Creates artifacts for generated images
- Can refine based on feedback

### Reel Agent:
- Understands natural language requests
- Generates reel scripts using Gemini 3 Pro
- Optionally generates videos using Veo 3.1
- Maintains conversation context
- Creates artifacts for generated content

### Scheduling:
- Links artifacts to scheduled posts
- Extracts content and media from artifacts
- Schedules posts for future publishing
- Supports notifications (if configured)

## Troubleshooting

### Issue: "Agent not found"
- **Solution**: Ensure agents are created in database. Check `/api/projects/{project_id}/agents`

### Issue: "GEMINI_API_KEY not configured"
- **Solution**: Set `GEMINI_API_KEY` in `.env` file

### Issue: "Conversation not found"
- **Solution**: Use `conversation_id` from previous chat response, or leave null to create new

### Issue: Image/Video generation fails
- **Solution**: Check Gemini API key is valid and has access to image/video models

### Issue: Scheduling doesn't work
- **Solution**: Ensure Celery worker is running (optional, for background tasks)

## Notes

- All endpoints require authentication (JWT token)
- All endpoints require a valid project_id
- Generated content is stored as artifacts
- Conversations maintain context across messages
- Scheduling works with or without Celery (falls back to database)
