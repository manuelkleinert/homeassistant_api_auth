import os
import json
from .api import AuthView, TokenCheckView, LogoutView
from homeassistant.helpers.discovery import async_load_platform

DOMAIN = "api_auth"

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

async def async_setup(hass, config):
    """Set up the api_auth component.

    - Register HTTP views.
    - Store the current state of ``input_select.api_extern_page`` in ``hass.data``.
    - Listen for changes to keep the internal flag in sync.
    - Load platforms.
    """
    config_dir = hass.config.config_dir
    await hass.async_add_executor_job(ensure_files_exist, config_dir)

    # Register HTTP API views
    hass.http.register_view(AuthView(hass))
    hass.http.register_view(TokenCheckView(hass))
    hass.http.register_view(LogoutView(hass))

    # Store the current state of the input_select in hass.data
    input_state = hass.states.get("input_select.api_extern_page")
    hass.data[DOMAIN] = {
        "api_extern_active": input_state.state == "true" if input_state else False
    }

    # Listen for state changes of the input_select
    async def _handle_input_change(event):
        new_state = event.data.get("new_state")
        if new_state and new_state.entity_id == "input_select.api_extern_page":
            hass.data[DOMAIN]["api_extern_active"] = new_state.state == "true"

    hass.bus.async_listen("state_changed", _handle_input_change)

    # Load platforms
    await async_load_platform(hass, "switch", DOMAIN, {}, config)
    await async_load_platform(hass, "select", DOMAIN, {}, config)

    return True