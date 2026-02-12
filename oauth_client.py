import time
import requests

class OAuthClient:
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        token_url: str = "https://oauth.simaster.ugm.ac.id/oauth/token",
        scope: str = "dataset.public.test.read",
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_url = token_url
        self.scope = scope

        self._token = None
        self._expires_at = 0

    def get_access_token(self):
        if not self._token or time.time() >= self._expires_at:
            self._fetch_token()
        return self._token

    def _fetch_token(self):
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": self.scope,
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }

        response = requests.post(
            self.token_url,
            data=data,
            headers=headers,
            timeout=15
        )

        if response.status_code != 200:
            raise Exception(
                f"OAuth token failed: {response.status_code} {response.text}"
            )

        payload = response.json()
        self._token = payload["access_token"]

        expires_in = payload.get("expires_in", 3600)
        self._expires_at = time.time() + expires_in - 30

    def auth_headers(self):
        return {
            "Authorization": f"Bearer {self.get_access_token()}"
        }
