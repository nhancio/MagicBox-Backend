# API Authentication & User Management - Testing Guide

## Overview of Endpoints

### 1. **Register** (`POST /api/auth/register`)
**Purpose**: Public endpoint for new users to create an account  
**Authentication**: ❌ Not required (public endpoint)  
**Auto-creates**: Tenant, User (with OWNER role), Default Project  
**Returns**: JWT token + user info

**Use Case**: When a new user wants to sign up for the first time

---

### 2. **Login** (`POST /api/auth/login`)
**Purpose**: Public endpoint for existing users to authenticate  
**Authentication**: ❌ Not required (public endpoint)  
**Auto-creates**: Default Project (if user doesn't have one)  
**Returns**: JWT token + user info

**Use Case**: When an existing user wants to sign in

---

### 3. **Create User** (`POST /api/users/`)
**Purpose**: Admin endpoint to create users with specific roles  
**Authentication**: ⚠️ Currently not required (should be admin-only)  
**Auto-creates**: Tenant (if not provided), User with specified role  
**Returns**: User info (NO token)

**Use Case**: When an admin wants to create users with specific roles (ADMIN, EDITOR, VIEWER)

---

### 4. **Get Current User Info** (`GET /api/users/me`)
**Purpose**: Get the authenticated user's own information  
**Authentication**: ✅ Required (Bearer token)  
**Returns**: Current user's info

**Use Case**: When user wants to see their own profile

---

## Test Payloads

### 1. Register (POST /api/auth/register)

**Endpoint**: `POST http://localhost:8000/api/auth/register`

**Request Body**:
```json
{
  "email": "newuser@example.com",
  "name": "New User",
  "password": "securepassword123"
}
```

**Response** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "newuser@example.com",
    "name": "New User",
    "tenant_id": "660e8400-e29b-41d4-a716-446655440000",
    "role": "OWNER"
  }
}
```

**What happens**:
- ✅ Creates a new tenant
- ✅ Creates user with role "OWNER"
- ✅ Creates default project
- ✅ Returns JWT token (use this for subsequent requests)

---

### 2. Login (POST /api/auth/login)

**Endpoint**: `POST http://localhost:8000/api/auth/login`

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "12345"
}
```

**Response** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "name": "User Name",
    "tenant_id": "660e8400-e29b-41d4-a716-446655440000",
    "role": "OWNER"
  }
}
```

**What happens**:
- ✅ Validates email and password
- ✅ Ensures user has a project (creates if missing)
- ✅ Returns JWT token

**Error Response** (401 Unauthorized):
```json
{
  "detail": "Invalid credentials"
}
```

---

### 3. Create User (POST /api/users/)

**Endpoint**: `POST http://localhost:8000/api/users/`

**Request Body**:
```json
{
  "email": "editor@example.com",
  "name": "Editor User",
  "password": "password123",
  "role": "EDITOR",
  "tenant_id": null
}
```

**With specific tenant**:
```json
{
  "email": "admin@example.com",
  "name": "Admin User",
  "password": "password123",
  "role": "ADMIN",
  "tenant_id": "660e8400-e29b-41d4-a716-446655440000"
}
```

**Response** (201 Created):
```json
{
  "id": "770e8400-e29b-41d4-a716-446655440000",
  "email": "editor@example.com",
  "name": "Editor User",
  "tenant_id": "660e8400-e29b-41d4-a716-446655440000",
  "role": "EDITOR"
}
```

**Note**: This endpoint does NOT return a token. The created user must login separately.

**Available Roles**:
- `OWNER` - Full access
- `ADMIN` - Administrative access
- `EDITOR` - Can edit content
- `VIEWER` - Read-only access

**What happens**:
- ✅ Creates user with specified role
- ✅ Auto-creates tenant if `tenant_id` is null/0
- ✅ Does NOT create default project
- ✅ Does NOT return token

---

### 4. Get Current User Info (GET /api/users/me)

**Endpoint**: `GET http://localhost:8000/api/users/me`

**Headers**:
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response** (200 OK):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "name": "User Name",
  "tenant_id": "660e8400-e29b-41d4-a716-446655440000",
  "role": "OWNER"
}
```

**Error Response** (401 Unauthorized):
```json
{
  "detail": "Invalid authentication credentials"
}
```

**What happens**:
- ✅ Validates JWT token
- ✅ Returns current authenticated user's info

---

## Testing Workflow

### Step 1: Register a New User
```bash
curl -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "testuser@example.com",
    "name": "Test User",
    "password": "testpass123"
  }'
```

**Save the `access_token` from response**

### Step 2: Use the Token for Protected Endpoints
```bash
curl -X GET "http://localhost:8000/api/users/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE"
```

### Step 3: Login (Alternative to Register)
```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "testuser@example.com",
    "password": "testpass123"
  }'
```

### Step 4: Create Additional Users (Admin Function)
```bash
curl -X POST "http://localhost:8000/api/users/" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "editor@example.com",
    "name": "Editor User",
    "password": "editorpass123",
    "role": "EDITOR"
  }'
```

---

## Key Differences Summary

| Feature | Register | Login | Create User | Get Current User |
|---------|----------|-------|-------------|------------------|
| **Auth Required** | ❌ No | ❌ No | ⚠️ Should be | ✅ Yes |
| **Returns Token** | ✅ Yes | ✅ Yes | ❌ No | ❌ No |
| **Auto-creates Project** | ✅ Yes | ✅ Yes* | ❌ No | ❌ No |
| **Role Assignment** | Always OWNER | N/A | Custom | N/A |
| **Use Case** | New signup | Existing user | Admin creates users | Get own info |

*Login auto-creates project only if user doesn't have one

---

## Swagger UI Testing

1. **Open Swagger**: Navigate to `http://localhost:8000/docs`

2. **Register/Login First**:
   - Use `/api/auth/register` or `/api/auth/login`
   - Copy the `access_token` from response

3. **Authorize**:
   - Click the **"Authorize"** button at the top
   - Enter: `Bearer <your_access_token>`
   - Click "Authorize"

4. **Test Protected Endpoints**:
   - Now you can test `/api/users/me` and other protected endpoints
   - The Bearer token will be automatically included in requests

---

## Common Errors

### 401 Unauthorized
- **Cause**: Missing or invalid Bearer token
- **Fix**: Login/Register first and use the returned token

### 400 Bad Request - "User already exists"
- **Cause**: Email already registered
- **Fix**: Use `/api/auth/login` instead, or use a different email

### 400 Bad Request - "Invalid role"
- **Cause**: Role doesn't exist in database
- **Fix**: Use one of: OWNER, ADMIN, EDITOR, VIEWER

### 403 Forbidden - "You don't have permission"
- **Cause**: Trying to access another user's data without admin role
- **Fix**: Use your own email or ensure you have ADMIN/OWNER role
