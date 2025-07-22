import requests
import urllib.parse
from decouple import config


class OAuthService:
    """Simple OAuth helper for Google and Meta."""

    PROVIDERS = {
        "google": {
            "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
            "token_url": "https://oauth2.googleapis.com/token",
            "profile_url": "https://www.googleapis.com/oauth2/v2/userinfo",
            "client_id": config("GOOGLE_CLIENT_ID", default=""),
            "client_secret": config("GOOGLE_CLIENT_SECRET", default=""),
            "scope": "openid email profile",
        },
        "meta": {
            "auth_url": "https://www.facebook.com/v10.0/dialog/oauth",
            "token_url": "https://graph.facebook.com/v10.0/oauth/access_token",
            "profile_url": "https://graph.facebook.com/me?fields=id,name,email,picture",
            "client_id": config("META_CLIENT_ID", default=""),
            "client_secret": config("META_CLIENT_SECRET", default=""),
            "scope": "email public_profile",
        },
    }

    @classmethod
    def get_auth_url(cls, provider: str, state: str, redirect_uri: str) -> str:
        cfg = cls.PROVIDERS[provider]
        params = {
            "client_id": cfg["client_id"],
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": cfg["scope"],
            "state": state,
        }
        return f"{cfg['auth_url']}?{urllib.parse.urlencode(params)}"

    @classmethod
    def exchange_code(cls, provider: str, code: str, redirect_uri: str) -> dict:
        cfg = cls.PROVIDERS[provider]
        data = {
            "client_id": cfg["client_id"],
            "client_secret": cfg["client_secret"],
            "code": code,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }
        response = requests.post(cfg["token_url"], data=data, timeout=10)
        response.raise_for_status()
        return response.json()

    @classmethod
    def fetch_profile(cls, provider: str, access_token: str) -> dict:
        cfg = cls.PROVIDERS[provider]
        response = requests.get(
            cfg["profile_url"], params={"access_token": access_token}, timeout=10
        )
        response.raise_for_status()
        return response.json()
