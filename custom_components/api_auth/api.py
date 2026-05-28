from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant
import json
import bcrypt
import secrets
import time
import os
import asyncio

# ---------- Helpers ----------
def load_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception:
        return default


def save_json(path, data):
    try:
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


def load_users_full(config_dir):
    path = os.path.join(config_dir, "api_users.json")
    users = load_json(path, [])
    by_username = {u["username"]: u for u in users}
    by_id = {u["id"]: u for u in users}
    return by_username, by_id


def load_tokens(config_dir):
    path = os.path.join(config_dir, "api_tokens.json")
    return load_json(path, {})


def save_tokens(config_dir, tokens):
    path = os.path.join(config_dir, "api_tokens.json")
    save_json(path, tokens)


def cleanup_tokens(tokens):
    now = int(time.time())
    return {t: v for t, v in tokens.items() if v.get("expires", 0) > now}


# ---------- LOGIN ----------

class AuthView(HomeAssistantView):
    url = "/api/auth"
    name = "api:auth"
    requires_auth = False

    def __init__(self, hass: HomeAssistant):
        self.hass = hass

    async def post(self, request):
        try:
            data = await request.json()
        except Exception:
            return self.json({"success": False, "error": "invalid json"}, status_code=400)

        username = data.get("username")
        password = data.get("password")

        if not username or not password:
            return self.json({"success": False}, status_code=400)

        config_dir = self.hass.config.config_dir
        users_by_username, _ = await self.hass.async_add_executor_job(
            load_users_full, config_dir
        )
        user = users_by_username.get(username)

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
        token = secrets.token_hex(32)
        expires = int(time.time()) + (7 * 24 * 60 * 60)

        tokens = await self.hass.async_add_executor_job(load_tokens, config_dir)
        tokens = cleanup_tokens(tokens)

        tokens[token] = {
            "user_id": user["id"],
            "expires": expires
        }

        await self.hass.async_add_executor_job(save_tokens, config_dir, tokens)

        return self.json({
            "success": True,
            "token": token,
            "expires": expires
        })


# ---------- TOKEN CHECK ----------

class TokenCheckView(HomeAssistantView):
    url = "/api/check_token"
    name = "api:check_token"
    requires_auth = False

    def __init__(self, hass: HomeAssistant):
        self.hass = hass

    async def post(self, request):
        try:
            data = await request.json()
        except Exception:
            return self.json({"success": False}, status_code=400)

        token = data.get("token")
        if not token:
            return self.json({"success": False}, status_code=400)

        config_dir = self.hass.config.config_dir
        tokens = await self.hass.async_add_executor_job(load_tokens, config_dir)
        tokens = cleanup_tokens(tokens)

        token_data = tokens.get(token)

        if not token_data:
            return self.json({"success": False}, status_code=401)

        _, users_by_id = await self.hass.async_add_executor_job(
            load_users_full, config_dir
        )
        user = users_by_id.get(token_data["user_id"])

        if not user:
            return self.json({"success": False}, status_code=401)

        # Cleanup speichern
        await self.hass.async_add_executor_job(save_tokens, config_dir, tokens)

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

    def __init__(self, hass: HomeAssistant):
        self.hass = hass

    async def post(self, request):
        try:
            data = await request.json()
        except Exception:
            return self.json({"success": False}, status_code=400)

        token = data.get("token")
        if not token:
            return self.json({"success": False}, status_code=400)

        config_dir = self.hass.config.config_dir
        tokens = await self.hass.async_add_executor_job(load_tokens, config_dir)

        if token in tokens:
            del tokens[token]
            await self.hass.async_add_executor_job(save_tokens, config_dir, tokens)

        return self.json({"success": True})