import logging
from homeassistant.components.switch import SwitchEntity

_LOGGER = logging.getLogger(__name__)


DOMAIN = "api_auth"

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the switch platform.

    This adds a single switch that mirrors the state of the
    ``input_select.api_extern_page`` entity.
    """
    async_add_entities([ApiExternPageSwitch(hass)])
    return True


class ApiExternPageSwitch(SwitchEntity):
    """Switch entity linked to the ``input_select.api_extern_page`` input select.

    Turning the switch on/off will set the corresponding option on the input
    select and keep the internal state in sync via the listener defined in the
    component's ``__init__.py``.
    """

    def __init__(self, hass):
        self.hass = hass
        self._attr_name = "API Extern Page"
        self._attr_unique_id = "api_extern_page_switch"
        # Initial state based on the data stored by the component listener
        self._attr_is_on = hass.data.get(DOMAIN, {}).get("api_extern_active", False)

    @property
    def is_on(self) -> bool:
        return self._attr_is_on

    async def async_turn_on(self, **kwargs):
        """Turn the switch on by selecting the ``true`` option."""
        try:
            await self.hass.services.async_call(
                "input_select",
                "select_option",
                {"entity_id": "input_select.api_extern_page", "option": "true"},
                blocking=True,
            )
            self._attr_is_on = True
            self.async_write_ha_state()
        except Exception as err:
            _LOGGER.error("Failed to turn on API Extern Page switch: %s", err)

    async def async_turn_off(self, **kwargs):
        """Turn the switch off by selecting the ``false`` option."""
        try:
            await self.hass.services.async_call(
                "input_select",
                "select_option",
                {"entity_id": "input_select.api_extern_page", "option": "false"},
                blocking=True,
            )
            self._attr_is_on = False
            self.async_write_ha_state()
        except Exception as err:
            _LOGGER.error("Failed to turn off API Extern Page switch: %s", err)
