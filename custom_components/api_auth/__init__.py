import os
import json

CONFIG_PATH = "/config"
USERS_FILE = os.path.join(CONFIG_PATH, "api_users.json")
TOKENS_FILE = os.path.join(CONFIG_PATH, "api_tokens.json")


def ensure_files_exist():
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w") as f:
            json.dump([], f, indent=2)

    if not os.path.exists(TOKENS_FILE):
        with open(TOKENS_FILE, "w") as f:
            json.dump({}, f, indent=2)


async def async_setup(hass, config):
    ensure_files_exist()
    return True