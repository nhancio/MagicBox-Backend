# Swagger UI Authentication Troubleshooting

## ✅ Authentication is Working!

The test script confirms:
- Login works correctly
- Token validation works
- Your user has ADMIN role (can create users)

## Common Issues & Solutions

### Issue 1: "401 Unauthorized" in Swagger UI

**Problem**: Token not being sent correctly

**Solution 1: Try entering token WITHOUT "Bearer" prefix**
1. Click "Authorize" button in Swagger UI
2. In the "Value" field, enter **ONLY the token** (no "Bearer" prefix)
   ```
   eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI4Z...
   ```
3. Click "Authorize", then "Close"
4. Try the endpoint again

**Solution 2: Try entering token WITH "Bearer" prefix**
1. Click "Authorize" button
2. In the "Value" field, enter: `Bearer <your_token>`
   ```
   Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI4Z...
   ```
   **Important**: Make sure there's a **SPACE** after "Bearer"
3. Click "Authorize", then "Close"
4. Try the endpoint again

**Solution 3: Check if token is expired**
- Tokens expire after 24 hours
- Login again to get a fresh token

### Issue 2: Token appears to be set but still getting 401

**Check the Request Headers:**
1. In Swagger UI, after clicking "Try it out", look at the "Curl" command
2. Verify it includes: `-H "Authorization: Bearer <token>"`
3. If it shows `-H "Authorization: Bearer Bearer <token>"`, you entered it with "Bearer" prefix when Swagger already adds it

**Solution**: Clear authorization and re-enter token WITHOUT "Bearer" prefix

### Issue 3: "Only ADMIN and OWNER roles can create users"

**Problem**: Your user doesn't have the required role

**Check your role:**
1. Call `GET /api/users/me` (this should work with your token)
2. Check the `role` field in the response
3. If role is "EDITOR" or "VIEWER", you need to:
   - Use a user with OWNER or ADMIN role, OR
   - Have an admin update your role

**Your current user has ADMIN role** (from test script), so this shouldn't be an issue.

## Step-by-Step Testing Guide

### Step 1: Get a Fresh Token
```bash
POST /api/auth/login
{
  "email": "user@example.com",
  "password": "12345"
}
```

Copy the `access_token` from response.

### Step 2: Authorize in Swagger
1. Click the **"Authorize"** button (🔒 icon) at the top right
2. You'll see a modal with "Available authorizations"
3. In the "Value" field, paste your token
4. **Try both methods:**
   - Method A: Just the token (no "Bearer")
   - Method B: `Bearer <token>` (with space)
5. Click "Authorize"
6. You should see a green checkmark ✅
7. Click "Close"

### Step 3: Verify Authorization
1. Try `GET /api/users/me` first (simpler endpoint)
2. Click "Try it out"
3. Click "Execute"
4. If you get 200 OK with user data, authorization is working!

### Step 4: Create User
1. Now try `POST /api/users/`
2. Enter the payload:
```json
{
  "email": "editor@example.com",
  "name": "Editor User",
  "password": "password123",
  "role": "EDITOR",
  "tenant_id": null
}
```
3. Click "Execute"
4. Should return 201 Created with user data

## Alternative: Use cURL to Test

If Swagger UI continues to have issues, test with cURL:

```bash
# 1. Login and save token
TOKEN=$(curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"12345"}' \
  | python -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

# 2. Test get current user
curl -X GET "http://localhost:8000/api/users/me" \
  -H "Authorization: Bearer $TOKEN"

# 3. Create user
curl -X POST "http://localhost:8000/api/users/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "editor@example.com",
    "name": "Editor User",
    "password": "password123",
    "role": "EDITOR",
    "tenant_id": null
  }'
```

## Debugging: Check What's Being Sent

In Swagger UI, after clicking "Try it out":
1. Scroll down to see the "Curl" command
2. Check the Authorization header
3. It should look like: `-H "Authorization: Bearer eyJhbGci..."`
4. If you see `Bearer Bearer`, you entered it with prefix when Swagger adds it automatically

## Still Not Working?

Run the test script to verify everything works:
```bash
cd backend
python test_auth.py
```

This will:
- Test login
- Test token validation
- Show you the exact token to use
- Verify your role permissions
