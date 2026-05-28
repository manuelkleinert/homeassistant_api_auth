import os
import json
import logging
from .api import AuthView, TokenCheckView, LogoutView
from .storage import APIAuthStorage
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

DOMAIN = "api_auth"
PLATFORMS = ["switch", "sensor"]

def migrate_and_init_storage(config_dir):
    """Migrate JSON data to SQLite and initialize storage."""
    storage = APIAuthStorage(config_dir)

    users_file = os.path.join(config_dir, "api_users.json")
    tokens_file = os.path.join(config_dir, "api_tokens.json")

    # Migrate users
    if os.path.exists(users_file):
        try:
            with open(users_file, "r") as f:
                users = json.load(f)
            for user in users:
                # Add user directly to DB (passwords are already hashed)
                with storage._get_connection() as conn:
                    conn.execute(
                        "INSERT OR IGNORE INTO users (id, username, password, role) VALUES (?, ?, ?, ?)",
                        (user["id"], user["username"], user["password"], user.get("role", "user"))
                    )
            os.remove(users_file)
            _LOGGER.info("Migrated users from JSON to SQLite")
        except Exception as err:
            _LOGGER.error("Failed to migrate users: %s", err)

    # Migrate tokens
    if os.path.exists(tokens_file):
        try:
            with open(tokens_file, "r") as f:
                tokens = json.load(f)
            for token, data in tokens.items():
                with storage._get_connection() as conn:
                    conn.execute(
                        "INSERT OR IGNORE INTO tokens (token, user_id, expires) VALUES (?, ?, ?)",
                        (token, data["user_id"], data["expires"])
                    )
            os.remove(tokens_file)
            _LOGGER.info("Migrated tokens from JSON to SQLite")
        except Exception as err:
            _LOGGER.error("Failed to migrate tokens: %s", err)

    return storage

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the api_auth component."""
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up API Auth from a config entry."""
    config_dir = hass.config.config_dir
    storage = await hass.async_add_executor_job(migrate_and_init_storage, config_dir)

    # Register HTTP API views
    hass.http.register_view(AuthView(hass, storage))
    hass.http.register_view(TokenCheckView(hass, storage))
    hass.http.register_view(LogoutView(hass, storage))

    # Initialize shared data
    hass.data[DOMAIN] = {
        "api_extern_active": False,
        "storage": storage
    }

    # Forward the setup to the platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register update listener for options
    entry.async_on_unload(entry.add_update_listener(update_listener))

    return True

async def update_listener(hass: HomeAssistant, entry: ConfigEntry):
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data.pop(DOMAIN)

    return unload_ok