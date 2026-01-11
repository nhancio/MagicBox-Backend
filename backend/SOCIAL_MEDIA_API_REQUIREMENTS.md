# Social Media Platform API Requirements

## Overview
This document outlines the APIs, credentials, and permissions needed for each social media platform integration.

## 1. Facebook & Instagram (Meta)

### Required APIs
- **Facebook Graph API** - For posting to Facebook pages
- **Instagram Graph API** - For posting to Instagram Business accounts
- **Facebook Login** - OAuth 2.0 authentication

### Setup Steps
1. Create a Facebook App at https://developers.facebook.com/
2. Add products: "Facebook Login" and "Instagram Graph API"
3. Configure OAuth redirect URIs
4. Get App ID and App Secret

### Credentials Needed
```
FACEBOOK_APP_ID=your_app_id
FACEBOOK_APP_SECRET=your_app_secret
```

### OAuth Flow
1. User authorizes via Facebook Login
2. Exchange code for access token
3. Get long-lived token (60 days)
4. Store token in `social_accounts` table

### Permissions Required
- `pages_manage_posts` - Post to Facebook pages
- `pages_read_engagement` - Read post analytics
- `instagram_basic` - Access Instagram account
- `instagram_content_publish` - Publish to Instagram
- `business_management` - Manage business accounts

### API Endpoints We'll Use
- `POST /{page-id}/feed` - Create Facebook post
- `POST /{ig-user-id}/media` - Create Instagram media container
- `POST /{ig-user-id}/media_publish` - Publish Instagram post
- `GET /{page-id}/insights` - Get analytics

**Documentation:** https://developers.facebook.com/docs/graph-api

---

## 2. YouTube

### Required APIs
- **YouTube Data API v3** - For uploading videos and managing content
- **YouTube OAuth 2.0** - For authentication

### Setup Steps
1. Create a project in Google Cloud Console
2. Enable YouTube Data API v3
3. Create OAuth 2.0 credentials
4. Configure authorized redirect URIs

### Credentials Needed
```
YOUTUBE_CLIENT_ID=your_client_id
YOUTUBE_CLIENT_SECRET=your_client_secret
```

### OAuth Flow
1. User authorizes via Google OAuth
2. Exchange code for access token and refresh token
3. Store tokens in `social_accounts` table
4. Use refresh token to get new access tokens

### Permissions Required (Scopes)
- `https://www.googleapis.com/auth/youtube.upload` - Upload videos
- `https://www.googleapis.com/auth/youtube.readonly` - Read channel info
- `https://www.googleapis.com/auth/youtube.force-ssl` - Manage videos

### API Endpoints We'll Use
- `POST /youtube/v3/videos` - Upload video
- `POST /youtube/v3/playlists` - Create/manage playlists
- `GET /youtube/v3/channels` - Get channel info
- `GET /youtube/v3/analytics/reports` - Get analytics

**Documentation:** https://developers.google.com/youtube/v3

---

## 3. LinkedIn

### Required APIs
- **LinkedIn API v2** - For posting content
- **LinkedIn OAuth 2.0** - For authentication

### Setup Steps
1. Create a LinkedIn App at https://www.linkedin.com/developers/
2. Request access to Marketing Developer Platform
3. Get Client ID and Client Secret
4. Configure redirect URIs

### Credentials Needed
```
LINKEDIN_CLIENT_ID=your_client_id
LINKEDIN_CLIENT_SECRET=your_client_secret
```

### OAuth Flow
1. User authorizes via LinkedIn OAuth
2. Exchange code for access token
3. Store token in `social_accounts` table
4. Tokens expire in 60 days (need refresh)

### Permissions Required (Scopes)
- `w_member_social` - Post on behalf of user
- `r_liteprofile` - Read basic profile
- `r_emailaddress` - Read email address
- `w_organization_social` - Post on behalf of organization (if applicable)

### API Endpoints We'll Use
- `POST /v2/ugcPosts` - Create post
- `POST /v2/shares` - Share content
- `GET /v2/me` - Get user info
- `GET /v2/organizationalEntityFollowerStatistics` - Get analytics

**Documentation:** https://learn.microsoft.com/en-us/linkedin/

---

## 4. Twitter/X

### Required APIs
- **Twitter API v2** - For posting tweets
- **Twitter OAuth 2.0** - For authentication

### Setup Steps
1. Apply for Twitter Developer account at https://developer.twitter.com/
2. Create a new App/Project
3. Get API Key, API Secret, Bearer Token
4. Set up OAuth 2.0

### Credentials Needed
```
TWITTER_API_KEY=your_api_key
TWITTER_API_SECRET=your_api_secret
TWITTER_BEARER_TOKEN=your_bearer_token (optional, for app-only auth)
```

### OAuth Flow
1. User authorizes via Twitter OAuth 2.0
2. Exchange code for access token
3. Store token in `social_accounts` table
4. Tokens don't expire (but can be revoked)

### Permissions Required (Scopes)
- `tweet.read` - Read tweets
- `tweet.write` - Post tweets
- `users.read` - Read user info
- `offline.access` - Refresh token capability

### API Endpoints We'll Use
- `POST /2/tweets` - Create tweet
- `POST /2/tweets/:id/retweets` - Retweet
- `GET /2/users/me` - Get user info
- `GET /2/tweets/:id` - Get tweet analytics

**Documentation:** https://developer.twitter.com/en/docs/twitter-api

---

## 5. TikTok

### Required APIs
- **TikTok Marketing API** - For uploading and publishing videos
- **TikTok OAuth 2.0** - For authentication

### Setup Steps
1. Apply for TikTok Marketing API access at https://developers.tiktok.com/
2. Create an app
3. Get Client Key and Client Secret
4. Configure redirect URIs

### Credentials Needed
```
TIKTOK_CLIENT_KEY=your_client_key
TIKTOK_CLIENT_SECRET=your_client_secret
```

### OAuth Flow
1. User authorizes via TikTok OAuth
2. Exchange code for access token
3. Store token in `social_accounts` table
4. Tokens expire (need refresh)

### Permissions Required (Scopes)
- Video upload
- Video publishing
- Analytics access

### API Endpoints We'll Use
- `POST /video/upload/` - Upload video
- `POST /video/publish/` - Publish video
- `GET /video/query/` - Get video info
- `GET /analytics/video/` - Get analytics

**Documentation:** https://developers.tiktok.com/

---

## Implementation Notes

### Token Storage
- Store access tokens and refresh tokens in `social_accounts` table
- Encrypt sensitive tokens before storing
- Implement token refresh logic for expired tokens

### Rate Limiting
Each platform has rate limits:
- **Facebook:** 200 calls/hour per user
- **Instagram:** 200 calls/hour per user
- **YouTube:** 10,000 units/day (quota system)
- **LinkedIn:** 500 calls/day per app
- **Twitter:** Varies by endpoint (300 tweets/3 hours)
- **TikTok:** Varies by endpoint

### Error Handling
- Handle token expiration
- Handle rate limit errors (429)
- Handle platform-specific errors
- Retry logic with exponential backoff

### Testing
- Use platform sandbox/test environments where available
- Test OAuth flows
- Test posting to test accounts
- Monitor API usage and quotas
