import os
import json
from fastapi import HTTPException

class Settings:
    def __init__(self):
        self.GOOGLE_CREDENTIALS_JSON = self._load_google_credentials()
        self.GEMINI_API_KEY = self._get_env_variable('GEMINI_API_KEY')

    def _get_env_variable(self, key: str) -> str:
        value = os.getenv(key)
        if not value:
            raise HTTPException(
                status_code=500,
                detail=f"Missing required environment variable: {key}"
            )
        return value

    def _load_google_credentials(self) -> str:
        path = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")
        if not os.path.exists(path):
            raise HTTPException(
                status_code=500,
                detail=f"Google credentials file not found at: {path}"
            )
        with open(path) as f:
            return json.load(f)

settings = Settings()
