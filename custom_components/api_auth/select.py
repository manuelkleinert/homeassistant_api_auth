import logging
from homeassistant.components.select import SelectEntity

_LOGGER = logging.getLogger(__name__)


DOMAIN = "api_auth"

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the select platform.

    This platform is loaded via ``async_load_platform`` from ``__init__.py``.
    It adds a single ``ApiExternPageSelect`` entity that mirrors the ``api_extern_active`` flag.
    """
    async_add_entities([ApiExternPageSelect(hass)])
    return True


class ApiExternPageSelect(SelectEntity):
    """Custom Select entity exposing ``true``/``false`` options.

    The state is stored in ``hass.data[DOMAIN]["api_extern_active"]`` and kept
    in sync by the listener defined in ``custom_components/api_auth/__init__.py``.
    """

    def __init__(self, hass):
        self.hass = hass
        self._attr_name = "API Extern Page (Select)"
        self._attr_unique_id = "api_extern_page_select"
        self._attr_options = ["true", "false"]
        # Initialise the current option based on the stored flag
        flag = hass.data.get(DOMAIN, {}).get("api_extern_active", False)
        self._attr_current_option = "true" if flag else "false"

    @property
    def current_option(self) -> str:
        return self._attr_current_option

    async def async_select_option(self, option: str) -> None:
        """Handle a user selecting an option.

        The chosen option updates the internal flag and writes the state back to
        ``hass.data`` so the switch entity stays synchronised.
        """
        if option not in self._attr_options:
            _LOGGER.error("Invalid option %s for API Extern Page select", option)
            return
        self._attr_current_option = option
        self.hass.data[DOMAIN]["api_extern_active"] = option == "true"
        self.async_write_ha_state()

    async def async_update(self) -> None:
        """Refresh the entity state from ``hass.data``.

        This method is called by Home Assistant periodically.
        """
        flag = self.hass.data.get(DOMAIN, {}).get("api_extern_active", False)
        self._attr_current_option = "true" if flag else "false"
