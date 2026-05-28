from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant
from .storage import APIAuthStorage
import bcrypt
import time
import logging

_LOGGER = logging.getLogger(__name__)

# ---------- LOGIN ----------

class AuthView(HomeAssistantView):
    url = "/api/auth"
    name = "api:auth"
    requires_auth = False

    def __init__(self, hass: HomeAssistant, storage: APIAuthStorage):
        self.hass = hass
        self.storage = storage

    async def post(self, request):
        try:
            data = await request.json()
        except Exception:
            return self.json({"success": False, "error": "invalid json"}, status_code=400)

        username = data.get("username")
        password = data.get("password")

        if not username or not password:
            return self.json({"success": False}, status_code=400)

        user = await self.hass.async_add_executor_job(
            self.storage.get_user_by_name, username
        )

        if not user:
            return self.json({"success": False}, status_code=401)

        # Passwort prüfen (sicher im Executor)
        try:
            is_valid = await self.hass.async_add_executor_job(
                bcrypt.checkpw, password.encode(), user["password"].encode()
            )
            if not is_valid:
                return self.json({"success": False}, status_code=401)
        except Exception:
            return self.json({"success": False, "error": "hash error"}, status_code=500)

        # Token erzeugen
        token_data = await self.hass.async_add_executor_job(
            self.storage.create_token, user["id"]
        )

        return self.json({
            "success": True,
            "token": token_data["token"],
            "expires": token_data["expires"]
        })


# ---------- TOKEN CHECK ----------

class TokenCheckView(HomeAssistantView):
    url = "/api/check_token"
    name = "api:check_token"
    requires_auth = False

    def __init__(self, hass: HomeAssistant, storage: APIAuthStorage):
        self.hass = hass
        self.storage = storage

    async def post(self, request):
        try:
            data = await request.json()
        except Exception:
            return self.json({"success": False}, status_code=400)

        token = data.get("token")
        if not token:
            return self.json({"success": False}, status_code=400)

        token_info = await self.hass.async_add_executor_job(
            self.storage.validate_token, token
        )

        if not token_info:
            return self.json({"success": False}, status_code=401)

        user_id, _ = token_info
        user = await self.hass.async_add_executor_job(
            self.storage.get_user_by_id, user_id
        )

        if not user:
            return self.json({"success": False}, status_code=401)

        return self.json({
            "success": True,
            "user_id": user["id"],
            "username": user["username"],
            "role": user.get("role", "user")
        })


# ---------- LOGOUT ----------

class LogoutView(HomeAssistantView):
    url = "/api/logout"
    name = "api:logout"
    requires_auth = False

    def __init__(self, hass: HomeAssistant, storage: APIAuthStorage):
        self.hass = hass
        self.storage = storage

    async def post(self, request):
        try:
            data = await request.json()
        except Exception:
            return self.json({"success": False}, status_code=400)

        token = data.get("token")
        if not token:
            return self.json({"success": False}, status_code=400)

        await self.hass.async_add_executor_job(
            self.storage.delete_token, token
        )

        return self.json({"success": True})