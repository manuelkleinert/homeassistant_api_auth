from homeassistant.components.http import HomeAssistantView
import json
import bcrypt
import secrets
import time
import os

CONFIG_PATH = "/config"
USERS_FILE = os.path.join(CONFIG_PATH, "api_users.json")
TOKENS_FILE = os.path.join(CONFIG_PATH, "api_tokens.json")

# ---------- Create Config Files if not exist ----------
def ensure_files_exist():
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w") as f:
            json.dump([], f, indent=2)

    if not os.path.exists(TOKENS_FILE):
        with open(TOKENS_FILE, "w") as f:
            json.dump({}, f, indent=2)

ensure_files_exist()

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


def load_users_full():
    users = load_json(USERS_FILE, [])
    by_username = {u["username"]: u for u in users}
    by_id = {u["id"]: u for u in users}
    return by_username, by_id


def load_tokens():
    return load_json(TOKENS_FILE, {})


def save_tokens(tokens):
    save_json(TOKENS_FILE, tokens)


def cleanup_tokens(tokens):
    now = int(time.time())
    return {t: v for t, v in tokens.items() if v.get("expires", 0) > now}


# ---------- LOGIN ----------

class AuthView(HomeAssistantView):
    url = "/api/auth"
    name = "api:auth"
    requires_auth = False

    async def post(self, request):
        try:
            data = await request.json()
        except Exception:
            return self.json({"success": False, "error": "invalid json"}, status_code=400)

        username = data.get("username")
        password = data.get("password")

        if not username or not password:
            return self.json({"success": False}, status_code=400)

        users_by_username, _ = load_users_full()
        user = users_by_username.get(username)

        if not user:
            return self.json({"success": False}, status_code=401)

        # Passwort prüfen (sicher)
        try:
            if not bcrypt.checkpw(password.encode(), user["password"].encode()):
                return self.json({"success": False}, status_code=401)
        except Exception:
            return self.json({"success": False, "error": "hash error"}, status_code=500)

        # Token erzeugen
        token = secrets.token_hex(32)
        expires = int(time.time()) + (7 * 24 * 60 * 60)

        tokens = load_tokens()
        tokens = cleanup_tokens(tokens)

        tokens[token] = {
            "user_id": user["id"],
            "expires": expires
        }

        save_tokens(tokens)

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

    async def post(self, request):
        try:
            data = await request.json()
        except Exception:
            return self.json({"success": False}, status_code=400)

        token = data.get("token")
        if not token:
            return self.json({"success": False}, status_code=400)

        tokens = load_tokens()
        tokens = cleanup_tokens(tokens)

        token_data = tokens.get(token)

        if not token_data:
            return self.json({"success": False}, status_code=401)

        _, users_by_id = load_users_full()
        user = users_by_id.get(token_data["user_id"])

        if not user:
            return self.json({"success": False}, status_code=401)

        # Cleanup speichern (wichtig!)
        save_tokens(tokens)

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

    async def post(self, request):
        try:
            data = await request.json()
        except Exception:
            return self.json({"success": False}, status_code=400)

        token = data.get("token")
        if not token:
            return self.json({"success": False}, status_code=400)

        tokens = load_tokens()

        if token in tokens:
            del tokens[token]
            save_tokens(tokens)

        return self.json({"success": True})