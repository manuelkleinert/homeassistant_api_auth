import os
import json
from .api import AuthView, TokenCheckView, LogoutView
from homeassistant.helpers.discovery import async_load_platform

CONFIG_PATH = "/config"
USERS_FILE = os.path.join(CONFIG_PATH, "api_users.json")
TOKENS_FILE = os.path.join(CONFIG_PATH, "api_tokens.json")

def ensure_files_exist():
    """Create empty user and token files if they do not exist."""
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w") as f:
            json.dump([], f, indent=2)
    if not os.path.exists(TOKENS_FILE):
        with open(TOKENS_FILE, "w") as f:
            json.dump({}, f, indent=2)

async def async_setup(hass, config):
    """Set up the api_auth component.

    - Register HTTP views.
    - Store the current state of ``input_select.api_extern_page`` in ``hass.data``.
    - Listen for changes to keep the internal flag in sync.
    - Load the switch platform so a UI toggle is available.
    """
    ensure_files_exist()

    # Register HTTP API views
    hass.http.register_view(AuthView())
    hass.http.register_view(TokenCheckView())
    hass.http.register_view(LogoutView())

    # Store the current state of the input_select in hass.data
    input_state = hass.states.get("input_select.api_extern_page")
    hass.data[__name__] = {
        "api_extern_active": input_state.state == "true" if input_state else False
    }

    # Listen for state changes of the input_select
    async def _handle_input_change(event):
        new_state = event.data.get("new_state")
        if new_state and new_state.entity_id == "input_select.api_extern_page":
            hass.data[__name__]["api_extern_active"] = new_state.state == "true"

    hass.bus.async_listen("state_changed", _handle_input_change)

    # Load the Switch platform so a UI toggle can be presented
    await async_load_platform(hass, "switch", "api_auth", {}, config)
    # Load the Select platform to expose a custom select entity
    await async_load_platform(hass, "select", "api_auth", {}, config)

    return True