import json
import os
import stat
from pathlib import Path


CONFIG_DIR = Path.home() / ".auth_manager"
CREDENTIALS_FILE = CONFIG_DIR / "credentials.json"


class AuthManager:
    def __init__(self):
        self.credentials: dict = {}
        self._loaded = False

    def setup(self) -> None:
        """Initialize config directory and credentials file."""
        CONFIG_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)

        if CREDENTIALS_FILE.exists():
            print(f"Auth manager already initialized at {CONFIG_DIR}")
            return

        self._write_credentials({})
        print(f"Auth manager initialized at {CONFIG_DIR}")
        print(f"Credentials file created: {CREDENTIALS_FILE}")

    def load(self) -> None:
        if not CREDENTIALS_FILE.exists():
            raise FileNotFoundError(
                f"Credentials file not found. Run setup first: {CREDENTIALS_FILE}"
            )
        with open(CREDENTIALS_FILE) as f:
            self.credentials = json.load(f)
        self._loaded = True

    def save(self, service: str, token: str) -> None:
        self._ensure_loaded()
        self.credentials[service] = token
        self._write_credentials(self.credentials)
        print(f"Credentials saved for service: {service}")

    def get(self, service: str) -> str | None:
        self._ensure_loaded()
        return self.credentials.get(service)

    def delete(self, service: str) -> bool:
        self._ensure_loaded()
        if service not in self.credentials:
            return False
        del self.credentials[service]
        self._write_credentials(self.credentials)
        print(f"Credentials removed for service: {service}")
        return True

    def list_services(self) -> list[str]:
        self._ensure_loaded()
        return list(self.credentials.keys())

    def _ensure_loaded(self) -> None:
        if not self._loaded:
            self.load()

    def _write_credentials(self, data: dict) -> None:
        CREDENTIALS_FILE.write_text(json.dumps(data, indent=2))
        CREDENTIALS_FILE.chmod(stat.S_IRUSR | stat.S_IWUSR)
