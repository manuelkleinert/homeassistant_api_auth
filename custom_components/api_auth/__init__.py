import os
import json
from .api import AuthView, TokenCheckView, LogoutView
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

DOMAIN = "api_auth"
PLATFORMS = ["switch", "select"]

def ensure_files_exist(config_dir):
    """Create empty user and token files if they do not exist."""
    users_file = os.path.join(config_dir, "api_users.json")
    tokens_file = os.path.join(config_dir, "api_tokens.json")

    if not os.path.exists(users_file):
        with open(users_file, "w") as f:
            json.dump([], f, indent=2)
    if not os.path.exists(tokens_file):
        with open(tokens_file, "w") as f:
            json.dump({}, f, indent=2)

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the api_auth component."""
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up API Auth from a config entry."""
    config_dir = hass.config.config_dir
    await hass.async_add_executor_job(ensure_files_exist, config_dir)

    # Register HTTP API views
    hass.http.register_view(AuthView(hass))
    hass.http.register_view(TokenCheckView(hass))
    hass.http.register_view(LogoutView(hass))

    # Initialize shared data
    hass.data[DOMAIN] = {
        "api_extern_active": False
    }

    # Forward the setup to the platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data.pop(DOMAIN)

    return unload_ok