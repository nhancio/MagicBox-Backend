# Implementation Plan: Conversational Marketing Content Generation Platform

## Overview
Transform the current API-based system into a conversational chatbot platform for marketing content generation (images, posts, reels/shorts) targeting small business and solo business users.

---

## Phase 1: Backend Architecture - Conversational Agent System

### 1.1 Chat Session Management
**Files to Create/Modify:**
- `backend/src/app/db/models/chat_session.py` - New model for chat sessions
- `backend/src/app/db/models/chat_message.py` - New model for chat messages
- `backend/src/app/db/repositories/chat_session_repo.py` - Repository for chat sessions
- `backend/src/app/db/repositories/chat_message_repo.py` - Repository for chat messages
- `backend/src/app/api/v1/chat_sessions.py` - API endpoints for chat sessions

**Key Features:**
- Each project can have multiple chat sessions
- Each session is tied to a specific agent (Image Agent or Reel Agent)
- Session metadata: title, created_at, updated_at, status
- Message threading and context preservation

### 1.2 Enhanced Memory System
**Files to Modify:**
- `backend/src/app/ai/memory/session_memory.py` - Enhance for chat-based context
- `backend/src/app/ai/memory/long_term_memory.py` - User preferences, brand guidelines
- `backend/src/app/ai/memory/episodic_memory.py` - Conversation history

**Key Features:**
- Per-session conversation history
- User brand preferences (colors, tone, style)
- Content generation history and patterns
- Context window management for long conversations

### 1.3 Conversational Agent Framework
**Files to Create/Modify:**
- `backend/src/app/ai/agents/conversational_base.py` - Base class for conversational agents
- `backend/src/app/ai/agents/image_chat_agent.py` - Conversational image generation agent
- `backend/src/app/ai/agents/reel_chat_agent.py` - Conversational reel/shorts generation agent
- `backend/src/app/ai/orchestrator/chat_orchestrator.py` - Multi-agent orchestration

**Key Features:**
- Natural language understanding for user requests
- Context-aware responses
- Multi-turn conversations
- File upload handling (images, videos, brand assets)
- Progressive content refinement

### 1.4 State Management System
**Files to Create:**
- `backend/src/app/services/state_manager.py` - Centralized state management
- `backend/src/app/db/models/agent_state.py` - Persistent agent state

**Key Features:**
- Track conversation flow state
- Store intermediate generation results
- Manage user preferences per project
- Handle draft content states

### 1.5 Agent Orchestration (LangGraph)
**Files to Create:**
- `backend/src/app/ai/orchestrator/langgraph_workflow.py` - LangGraph workflow definition
- `backend/src/app/ai/orchestrator/agent_nodes.py` - Individual agent nodes
- `backend/src/app/ai/orchestrator/workflow_state.py` - Workflow state management

**Key Features:**
- Multi-agent workflows (e.g., generate post → generate image → generate reel)
- Conditional routing based on user intent
- Parallel agent execution when needed
- Error handling and retry logic

---

## Phase 2: API Endpoints - Chat-Based Interface

### 2.1 Chat Session Endpoints
**File:** `backend/src/app/api/v1/chat_sessions.py`

**Endpoints:**
- `POST /projects/{project_id}/chat-sessions` - Create new chat session
- `GET /projects/{project_id}/chat-sessions` - List all sessions
- `GET /projects/{project_id}/chat-sessions/{session_id}` - Get session details
- `DELETE /projects/{project_id}/chat-sessions/{session_id}` - Delete session

### 2.2 Chat Message Endpoints
**File:** `backend/src/app/api/v1/chat_messages.py`

**Endpoints:**
- `POST /projects/{project_id}/chat-sessions/{session_id}/messages` - Send message
- `GET /projects/{project_id}/chat-sessions/{session_id}/messages` - Get message history
- `POST /projects/{project_id}/chat-sessions/{session_id}/messages/{message_id}/regenerate` - Regenerate response
- `DELETE /projects/{project_id}/chat-sessions/{session_id}/messages/{message_id}` - Delete message

### 2.3 Agent Interaction Endpoints
**File:** `backend/src/app/api/v1/agent_chat.py`

**Endpoints:**
- `POST /projects/{project_id}/agents/{agent_id}/chat` - Send message to agent
- `GET /projects/{project_id}/agents/{agent_id}/sessions` - Get agent chat sessions
- `POST /projects/{project_id}/agents/{agent_id}/upload` - Upload files to agent
- `POST /projects/{project_id}/agents/{agent_id}/generate` - Trigger content generation

### 2.4 Content Management Endpoints
**File:** `backend/src/app/api/v1/generated_content.py`

**Endpoints:**
- `GET /projects/{project_id}/content` - List all generated content
- `GET /projects/{project_id}/content/{content_id}` - Get content details
- `POST /projects/{project_id}/content/{content_id}/download` - Download content
- `POST /projects/{project_id}/content/{content_id}/publish` - Publish to social media
- `DELETE /projects/{project_id}/content/{content_id}` - Delete content

---

## Phase 3: Database Schema Updates

### 3.1 New Tables
```sql
-- Chat Sessions
CREATE TABLE chat_sessions (
    id VARCHAR PRIMARY KEY,
    project_id VARCHAR NOT NULL,
    agent_id VARCHAR NOT NULL,
    title VARCHAR,
    status VARCHAR, -- active, archived, deleted
    metadata JSONB, -- user preferences, brand guidelines
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Chat Messages
CREATE TABLE chat_messages (
    id VARCHAR PRIMARY KEY,
    session_id VARCHAR NOT NULL,
    role VARCHAR NOT NULL, -- user, assistant, system
    content TEXT NOT NULL,
    metadata JSONB, -- attachments, generation params
    parent_message_id VARCHAR, -- for threading
    created_at TIMESTAMP
);

-- Agent State
CREATE TABLE agent_states (
    id VARCHAR PRIMARY KEY,
    session_id VARCHAR NOT NULL,
    agent_id VARCHAR NOT NULL,
    state_data JSONB, -- current state, context, preferences
    updated_at TIMESTAMP
);

-- Generated Content
CREATE TABLE generated_content (
    id VARCHAR PRIMARY KEY,
    project_id VARCHAR NOT NULL,
    session_id VARCHAR NOT NULL,
    agent_id VARCHAR NOT NULL,
    content_type VARCHAR, -- image, post, reel, video
    content_data JSONB, -- file paths, metadata, generation params
    status VARCHAR, -- draft, ready, published
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### 3.2 Migration Files
- `migrations/versions/xxx_add_chat_tables.py`
- `migrations/versions/xxx_add_content_tables.py`

---

## Phase 4: Frontend - Chat-Based UI

### 4.1 Project Dashboard
**File:** `magicbox/src/pages/ProjectDashboard.tsx`

**Features:**
- Project overview
- Quick access to agents
- Recent chat sessions
- Generated content gallery

### 4.2 Agent Selection Page
**File:** `magicbox/src/pages/AgentsPage.tsx`

**Features:**
- Agent cards (Image Agent, Reel Agent)
- "What I need" / "What you get" descriptions
- Start new chat button
- Agent history sidebar

### 4.3 Chat Interface
**File:** `magicbox/src/pages/ChatPage.tsx`
**Components:**
- `magicbox/src/components/chat/ChatSidebar.tsx` - Session list
- `magicbox/src/components/chat/ChatMessages.tsx` - Message display
- `magicbox/src/components/chat/ChatInput.tsx` - Input bar with upload, templates
- `magicbox/src/components/chat/AgentCard.tsx` - Agent info card

**Features:**
- Real-time message streaming
- File upload (drag & drop)
- Template selection
- Output format selection
- Message regeneration
- Context-aware suggestions

### 4.4 Content Gallery
**File:** `magicbox/src/pages/ContentGallery.tsx`

**Features:**
- Grid view of generated content
- Filter by type (image, post, reel)
- Preview and download
- Publish to social media
- Edit/regenerate options

### 4.5 State Management (Frontend)
**Files:**
- `magicbox/src/contexts/ChatContext.tsx` - Chat state management
- `magicbox/src/contexts/ProjectContext.tsx` - Project state
- `magicbox/src/hooks/useChatSession.ts` - Chat session hook
- `magicbox/src/hooks/useAgent.ts` - Agent interaction hook

---

## Phase 5: Agent-Specific Features

### 5.1 Image Generation Agent
**Capabilities:**
- Understand user requirements in natural language
- Generate marketing images (social media posts, ads, banners)
- Support brand guidelines (colors, fonts, style)
- Multiple format outputs (Instagram post, Facebook ad, Twitter header)
- Iterative refinement based on feedback

**Conversation Flow:**
1. User: "Create an image for my coffee shop promotion"
2. Agent: Asks for details (promotion type, colors, text, style)
3. User: Provides details or uploads reference
4. Agent: Generates image, shows preview
5. User: "Make it more vibrant" or "Change the text"
6. Agent: Refines and regenerates

### 5.2 Reel/Shorts Generation Agent
**Capabilities:**
- Generate video scripts for reels/shorts
- Create video content using AI (Veo 3.1)
- Support multiple platforms (Instagram Reels, TikTok, YouTube Shorts)
- Music and timing suggestions
- Hook generation for engagement

**Conversation Flow:**
1. User: "Create a reel for my product launch"
2. Agent: Asks for product details, target audience, style
3. User: Provides information
4. Agent: Generates script, shows preview
5. User: "Make it shorter" or "Add a call to action"
6. Agent: Refines script and generates video

---

## Phase 6: Integration & Publishing

### 6.1 Social Media Publishing
**Files:**
- `backend/src/app/services/social_publisher.py` - Enhanced publishing service
- `backend/src/app/api/v1/publishing.py` - Publishing endpoints

**Features:**
- Connect social media accounts (Instagram, Facebook, TikTok, YouTube)
- Schedule posts
- Preview before publishing
- Analytics tracking

### 6.2 Export Options
**Features:**
- Download content (images, videos)
- Export to Google Drive, Dropbox
- Share via link
- Batch export

---

## Phase 7: User Experience Enhancements

### 7.1 Smart Suggestions
- Context-aware prompts
- Template recommendations
- Style suggestions based on industry
- Best practices tips

### 7.2 Brand Management
- Save brand guidelines (colors, fonts, tone)
- Apply automatically to all generations
- Brand asset library (logos, images)

### 7.3 Content History
- View all generated content
- Reuse and remix previous content
- Version control for iterations

---

## Technical Stack Summary

### Backend
- **Framework:** FastAPI
- **Database:** PostgreSQL with pgvector
- **AI/ML:** Google Gemini (text, image, video)
- **Orchestration:** LangGraph for multi-agent workflows
- **Memory:** Custom memory system + vector embeddings
- **Real-time:** WebSockets for streaming responses

### Frontend
- **Framework:** React + TypeScript
- **UI Library:** Shadcn UI (already in use)
- **State Management:** React Context + Zustand
- **Real-time:** WebSocket client
- **File Upload:** React Dropzone

---

## Implementation Order

1. **Week 1:** Database schema + Chat session/message models
2. **Week 2:** Conversational agent base + Image chat agent
3. **Week 3:** Reel chat agent + State management
4. **Week 4:** LangGraph orchestration
5. **Week 5:** Frontend chat interface
6. **Week 6:** Content gallery + Publishing
7. **Week 7:** Testing + Refinement

---

## Key Design Decisions

1. **Conversational First:** All interactions through chat, not forms
2. **Context Preservation:** Maintain full conversation history
3. **Progressive Refinement:** Allow iterative improvements
4. **Small Business Focus:** Simple, intuitive, no technical jargon
5. **Multi-format Support:** One agent, multiple output formats
6. **Brand Consistency:** Automatic application of brand guidelines

---

## Success Metrics

- User can create marketing content through natural conversation
- Generated content matches brand guidelines automatically
- Average time to generate content < 2 minutes
- User satisfaction with generated content > 80%
- Multi-turn conversation support (5+ turns)

---

## Next Steps

1. Review and approve this plan
2. Start with Phase 1 (Backend Architecture)
3. Iterate based on feedback
4. Deploy incrementally
