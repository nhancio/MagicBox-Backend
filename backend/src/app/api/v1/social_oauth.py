"""
Social OAuth API endpoints - production OAuth flows for connecting platforms.

Order requested:
1) Instagram+Facebook (Meta)
2) LinkedIn
3) YouTube (Google)
4) X/Twitter
"""

from __future__ import annotations

from datetime import datetime
import hashlib
import base64
import secrets
import urllib.parse
from typing import Optional, Dict, Any, List

import httpx
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.db.session import get_db
from app.db.models.user import User
from app.db.models.project import Project
from app.db.models.oauth_state import OAuthState
from app.db.models.social_account import SocialPlatform
from app.dependencies.auth import get_current_user, require_project
from app.services.social_service import SocialService


router = APIRouter(prefix="/social/oauth", tags=["Social OAuth"])


def _popup_close_html(success: bool, provider: str, message: str) -> str:
    # PostMessage allows frontend to refresh accounts after OAuth.
    # We scope to FRONTEND_PUBLIC_URL for safety.
    target_origin = settings.FRONTEND_PUBLIC_URL.rstrip("/")
    safe_message = message.replace("\\", "\\\\").replace("'", "\\'")
    return f"""<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <title>MagicBox OAuth</title>
  </head>
  <body style="font-family: system-ui; padding: 24px;">
    <h2>{'Connected' if success else 'Connection failed'}</h2>
    <p>{safe_message}</p>
    <script>
      (function() {{
        try {{
          if (window.opener) {{
            window.opener.postMessage({{
              type: 'magicbox_oauth',
              provider: '{provider}',
              success: {str(success).lower()},
              message: '{safe_message}'
            }}, '{target_origin}');
          }}
        }} catch (e) {{}}
        window.close();
      }})();
    </script>
    <p>You can close this window.</p>
  </body>
</html>
"""


def _create_state(
    db: Session,
    provider: str,
    current_user: User,
    current_project: Project,
    return_to: Optional[str],
    code_verifier: Optional[str] = None,
    extra_metadata: Optional[Dict[str, Any]] = None,
) -> OAuthState:
    state = OAuthState(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        project_id=current_project.id,
        provider=provider,
        return_to=return_to,
        code_verifier=code_verifier,
        extra_metadata=extra_metadata or {},
    )
    db.add(state)
    db.commit()
    db.refresh(state)
    return state


def _get_state(db: Session, state_id: str, provider: str) -> OAuthState:
    st = db.query(OAuthState).filter(OAuthState.id == state_id).first()
    if not st:
        raise HTTPException(status_code=400, detail="Invalid state")
    if st.provider != provider:
        raise HTTPException(status_code=400, detail="State provider mismatch")
    if st.is_used:
        raise HTTPException(status_code=400, detail="State already used")
    if st.expires_at and st.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="State expired")
    return st


# ---------------------------
# Meta (Facebook + Instagram)
# ---------------------------

@router.get("/meta/start")
def meta_start(
    platform: str = Query(default="instagram_facebook", description="instagram_facebook|facebook|instagram"),
    return_to: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    current_project: Project = Depends(require_project),
    db: Session = Depends(get_db),
):
    if not settings.FACEBOOK_APP_ID or not settings.FACEBOOK_APP_SECRET:
        raise HTTPException(status_code=500, detail="FACEBOOK_APP_ID/FACEBOOK_APP_SECRET not configured")

    redirect_uri = f"{settings.BACKEND_PUBLIC_URL.rstrip('/')}/api/social/oauth/meta/callback"
    st = _create_state(
        db=db,
        provider="meta",
        current_user=current_user,
        current_project=current_project,
        return_to=return_to,
        extra_metadata={"platform": platform},
    )

    # Scopes for page posting + Instagram business publishing
    scope = [
        "pages_show_list",
        "pages_read_engagement",
        "pages_manage_posts",
        "instagram_basic",
        "instagram_content_publish",
    ]

    params = {
        "client_id": settings.FACEBOOK_APP_ID,
        "redirect_uri": redirect_uri,
        "state": st.id,
        "response_type": "code",
        "scope": ",".join(scope),
    }

    url = "https://www.facebook.com/v18.0/dialog/oauth?" + urllib.parse.urlencode(params)
    return RedirectResponse(url=url, status_code=status.HTTP_302_FOUND)


@router.get("/meta/callback")
def meta_callback(
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    error_description: Optional[str] = None,
    db: Session = Depends(get_db),
):
    if error:
        return HTMLResponse(_popup_close_html(False, "meta", error_description or error), status_code=400)
    if not code or not state:
        return HTMLResponse(_popup_close_html(False, "meta", "Missing code/state"), status_code=400)

    st = _get_state(db, state, "meta")

    redirect_uri = f"{settings.BACKEND_PUBLIC_URL.rstrip('/')}/api/social/oauth/meta/callback"
    token_url = "https://graph.facebook.com/v18.0/oauth/access_token"

    try:
        token_resp = httpx.get(
            token_url,
            params={
                "client_id": settings.FACEBOOK_APP_ID,
                "client_secret": settings.FACEBOOK_APP_SECRET,
                "redirect_uri": redirect_uri,
                "code": code,
            },
            timeout=30.0,
        )
        token_resp.raise_for_status()
        token_data = token_resp.json()
        user_access_token = token_data.get("access_token")
        if not user_access_token:
            raise ValueError("No access_token returned by Meta")

        # Fetch managed pages (includes page access tokens)
        pages_resp = httpx.get(
            "https://graph.facebook.com/v18.0/me/accounts",
            params={"access_token": user_access_token, "fields": "id,name,access_token"},
            timeout=30.0,
        )
        pages_resp.raise_for_status()
        pages = pages_resp.json().get("data", []) or []

        connected: List[str] = []

        for page in pages:
            page_id = page.get("id")
            page_name = page.get("name") or "Facebook Page"
            page_token = page.get("access_token") or user_access_token
            if not page_id:
                continue

            # Connect FB page
            SocialService.connect_account_for_tenant_user(
                db=db,
                tenant_id=st.tenant_id,
                user_id=st.user_id,
                platform=SocialPlatform.FACEBOOK,
                account_name=page_name,
                access_token=page_token,
                refresh_token=None,
                account_id=page_id,
                metadata={"page_id": page_id},
            )
            connected.append(f"FACEBOOK:{page_name}")

            # Try to find Instagram business account linked to this page
            ig_resp = httpx.get(
                f"https://graph.facebook.com/v18.0/{page_id}",
                params={
                    "fields": "instagram_business_account{id,username}",
                    "access_token": page_token,
                },
                timeout=30.0,
            )
            if ig_resp.status_code == 200:
                ig_data = ig_resp.json().get("instagram_business_account")
                if ig_data and ig_data.get("id"):
                    ig_id = ig_data.get("id")
                    ig_username = ig_data.get("username") or f"IG:{page_name}"
                    SocialService.connect_account_for_tenant_user(
                        db=db,
                        tenant_id=st.tenant_id,
                        user_id=st.user_id,
                        platform=SocialPlatform.INSTAGRAM,
                        account_name=ig_username,
                        access_token=page_token,
                        refresh_token=None,
                        account_id=ig_id,
                        metadata={"instagram_account_id": ig_id, "page_id": page_id},
                    )
                    connected.append(f"INSTAGRAM:{ig_username}")

        st.is_used = True
        db.commit()

        msg = "Connected: " + (", ".join(connected) if connected else "No pages found. Ensure your Meta user manages a Page with an Instagram business account.")
        return HTMLResponse(_popup_close_html(True, "meta", msg))
    except Exception as e:
        return HTMLResponse(_popup_close_html(False, "meta", f"Meta OAuth failed: {str(e)}"), status_code=400)


# -----------
# LinkedIn
# -----------

@router.get("/linkedin/start")
def linkedin_start(
    return_to: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    current_project: Project = Depends(require_project),
    db: Session = Depends(get_db),
):
    if not settings.LINKEDIN_CLIENT_ID or not settings.LINKEDIN_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="LINKEDIN_CLIENT_ID/LINKEDIN_CLIENT_SECRET not configured")

    redirect_uri = f"{settings.BACKEND_PUBLIC_URL.rstrip('/')}/api/social/oauth/linkedin/callback"
    st = _create_state(db, "linkedin", current_user, current_project, return_to)

    scope = "r_liteprofile r_emailaddress w_member_social"
    params = {
        "response_type": "code",
        "client_id": settings.LINKEDIN_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "state": st.id,
        "scope": scope,
    }
    url = "https://www.linkedin.com/oauth/v2/authorization?" + urllib.parse.urlencode(params)
    return RedirectResponse(url=url, status_code=status.HTTP_302_FOUND)


@router.get("/linkedin/callback")
def linkedin_callback(
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    error_description: Optional[str] = None,
    db: Session = Depends(get_db),
):
    if error:
        return HTMLResponse(_popup_close_html(False, "linkedin", error_description or error), status_code=400)
    if not code or not state:
        return HTMLResponse(_popup_close_html(False, "linkedin", "Missing code/state"), status_code=400)

    st = _get_state(db, state, "linkedin")
    redirect_uri = f"{settings.BACKEND_PUBLIC_URL.rstrip('/')}/api/social/oauth/linkedin/callback"

    try:
        token_resp = httpx.post(
            "https://www.linkedin.com/oauth/v2/accessToken",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
                "client_id": settings.LINKEDIN_CLIENT_ID,
                "client_secret": settings.LINKEDIN_CLIENT_SECRET,
            },
            timeout=30.0,
        )
        token_resp.raise_for_status()
        token_data = token_resp.json()
        access_token = token_data.get("access_token")
        if not access_token:
            raise ValueError("No access_token returned by LinkedIn")

        # Fetch profile
        me = httpx.get(
            "https://api.linkedin.com/v2/me",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=30.0,
        )
        me.raise_for_status()
        me_data = me.json()
        account_id = me_data.get("id")
        account_name = "LinkedIn"
        if me_data.get("localizedFirstName") or me_data.get("localizedLastName"):
            account_name = f"{me_data.get('localizedFirstName','').strip()} {me_data.get('localizedLastName','').strip()}".strip() or "LinkedIn"

        SocialService.connect_account_for_tenant_user(
            db=db,
            tenant_id=st.tenant_id,
            user_id=st.user_id,
            platform=SocialPlatform.LINKEDIN,
            account_name=account_name,
            access_token=access_token,
            refresh_token=None,
            account_id=account_id,
            metadata={"profile": me_data},
        )

        st.is_used = True
        db.commit()
        return HTMLResponse(_popup_close_html(True, "linkedin", f"Connected LinkedIn: {account_name}"))
    except Exception as e:
        return HTMLResponse(_popup_close_html(False, "linkedin", f"LinkedIn OAuth failed: {str(e)}"), status_code=400)


# -------
# YouTube
# -------

@router.get("/youtube/start")
def youtube_start(
    return_to: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    current_project: Project = Depends(require_project),
    db: Session = Depends(get_db),
):
    if not settings.YOUTUBE_CLIENT_ID or not settings.YOUTUBE_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="YOUTUBE_CLIENT_ID/YOUTUBE_CLIENT_SECRET not configured")

    redirect_uri = f"{settings.BACKEND_PUBLIC_URL.rstrip('/')}/api/social/oauth/youtube/callback"
    st = _create_state(db, "youtube", current_user, current_project, return_to)

    params = {
        "client_id": settings.YOUTUBE_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "https://www.googleapis.com/auth/youtube.upload",
        "access_type": "offline",
        "prompt": "consent",
        "state": st.id,
        "include_granted_scopes": "true",
    }
    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(params)
    return RedirectResponse(url=url, status_code=status.HTTP_302_FOUND)


@router.get("/youtube/callback")
def youtube_callback(
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    error_description: Optional[str] = None,
    db: Session = Depends(get_db),
):
    if error:
        return HTMLResponse(_popup_close_html(False, "youtube", error_description or error), status_code=400)
    if not code or not state:
        return HTMLResponse(_popup_close_html(False, "youtube", "Missing code/state"), status_code=400)

    st = _get_state(db, state, "youtube")
    redirect_uri = f"{settings.BACKEND_PUBLIC_URL.rstrip('/')}/api/social/oauth/youtube/callback"

    try:
        token_resp = httpx.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": settings.YOUTUBE_CLIENT_ID,
                "client_secret": settings.YOUTUBE_CLIENT_SECRET,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
            timeout=30.0,
        )
        token_resp.raise_for_status()
        token_data = token_resp.json()
        access_token = token_data.get("access_token")
        refresh_token = token_data.get("refresh_token")
        if not access_token:
            raise ValueError("No access_token returned by Google")

        SocialService.connect_account_for_tenant_user(
            db=db,
            tenant_id=st.tenant_id,
            user_id=st.user_id,
            platform=SocialPlatform.YOUTUBE,
            account_name="YouTube",
            access_token=access_token,
            refresh_token=refresh_token,
            account_id=None,
            metadata={"token_type": token_data.get("token_type"), "scope": token_data.get("scope")},
        )

        st.is_used = True
        db.commit()
        return HTMLResponse(_popup_close_html(True, "youtube", "Connected YouTube"))
    except Exception as e:
        return HTMLResponse(_popup_close_html(False, "youtube", f"YouTube OAuth failed: {str(e)}"), status_code=400)


# ----------
# X / Twitter
# ----------

def _pkce_pair() -> tuple[str, str]:
    verifier = secrets.token_urlsafe(48)
    digest = hashlib.sha256(verifier.encode("utf-8")).digest()
    challenge = base64.urlsafe_b64encode(digest).decode("utf-8").rstrip("=")
    return verifier, challenge


@router.get("/twitter/start")
def twitter_start(
    return_to: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    current_project: Project = Depends(require_project),
    db: Session = Depends(get_db),
):
    # Twitter OAuth2 uses client_id/client_secret (often different from API key/secret).
    # We'll reuse TWITTER_API_KEY / TWITTER_API_SECRET for now.
    if not settings.TWITTER_API_KEY or not settings.TWITTER_API_SECRET:
        raise HTTPException(status_code=500, detail="TWITTER_API_KEY/TWITTER_API_SECRET not configured")

    redirect_uri = f"{settings.BACKEND_PUBLIC_URL.rstrip('/')}/api/social/oauth/twitter/callback"
    verifier, challenge = _pkce_pair()
    st = _create_state(db, "twitter", current_user, current_project, return_to, code_verifier=verifier)

    params = {
        "response_type": "code",
        "client_id": settings.TWITTER_API_KEY,
        "redirect_uri": redirect_uri,
        "scope": "tweet.read tweet.write users.read offline.access",
        "state": st.id,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    }
    url = "https://twitter.com/i/oauth2/authorize?" + urllib.parse.urlencode(params)
    return RedirectResponse(url=url, status_code=status.HTTP_302_FOUND)


@router.get("/twitter/callback")
def twitter_callback(
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    error_description: Optional[str] = None,
    db: Session = Depends(get_db),
):
    if error:
        return HTMLResponse(_popup_close_html(False, "twitter", error_description or error), status_code=400)
    if not code or not state:
        return HTMLResponse(_popup_close_html(False, "twitter", "Missing code/state"), status_code=400)

    st = _get_state(db, state, "twitter")
    redirect_uri = f"{settings.BACKEND_PUBLIC_URL.rstrip('/')}/api/social/oauth/twitter/callback"

    try:
        basic = base64.b64encode(f"{settings.TWITTER_API_KEY}:{settings.TWITTER_API_SECRET}".encode("utf-8")).decode("utf-8")
        token_resp = httpx.post(
            "https://api.twitter.com/2/oauth2/token",
            headers={
                "Authorization": f"Basic {basic}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
                "code_verifier": st.code_verifier,
            },
            timeout=30.0,
        )
        token_resp.raise_for_status()
        token_data = token_resp.json()
        access_token = token_data.get("access_token")
        refresh_token = token_data.get("refresh_token")
        if not access_token:
            raise ValueError("No access_token returned by Twitter")

        # Fetch user to name the account
        me = httpx.get(
            "https://api.twitter.com/2/users/me",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=30.0,
        )
        me.raise_for_status()
        me_data = me.json().get("data") or {}
        account_id = me_data.get("id")
        account_name = me_data.get("username") or me_data.get("name") or "X"

        SocialService.connect_account_for_tenant_user(
            db=db,
            tenant_id=st.tenant_id,
            user_id=st.user_id,
            platform=SocialPlatform.TWITTER,
            account_name=str(account_name),
            access_token=access_token,
            refresh_token=refresh_token,
            account_id=account_id,
            metadata={"user": me_data, "scope": token_data.get("scope")},
        )

        st.is_used = True
        db.commit()
        return HTMLResponse(_popup_close_html(True, "twitter", f"Connected X/Twitter: {account_name}"))
    except Exception as e:
        return HTMLResponse(_popup_close_html(False, "twitter", f"Twitter OAuth failed: {str(e)}"), status_code=400)

