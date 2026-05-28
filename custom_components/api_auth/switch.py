import logging
from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.dispatcher import async_dispatcher_connect, async_dispatcher_send

_LOGGER = logging.getLogger(__name__)

DOMAIN = "api_auth"
SIGNAL_STATE_UPDATED = f"{DOMAIN}_state_updated"

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the switch platform from a config entry."""
    async_add_entities([ApiExternPageSwitch(hass)])
    return True


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the switch platform (legacy)."""
    async_add_entities([ApiExternPageSwitch(hass)])
    return True


class ApiExternPageSwitch(SwitchEntity, RestoreEntity):
    """Switch entity with internal state persistence."""

    def __init__(self, hass):
        self.hass = hass
        self._attr_name = "API Extern Page"
        self._attr_unique_id = "api_extern_page_switch"
        self._attr_is_on = False

    async def async_added_to_hass(self) -> None:
        """Handle when entity is added."""
        await super().async_added_to_hass()
        
        # Restore last state
        last_state = await self.async_get_last_state()
        if last_state:
            self._attr_is_on = (last_state.state == "on")
            self.hass.data[DOMAIN]["api_extern_active"] = self._attr_is_on

        # Listen for updates from the select
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, SIGNAL_STATE_UPDATED, self._update_state
            )
        )

    async def _update_state(self) -> None:
        """Update state when notified by dispatcher."""
        self._attr_is_on = self.hass.data[DOMAIN].get("api_extern_active", False)
        self.async_write_ha_state()

    @property
    def is_on(self) -> bool:
        return self._attr_is_on

    async def async_turn_on(self, **kwargs):
        """Turn the switch on."""
        self._attr_is_on = True
        self.hass.data[DOMAIN]["api_extern_active"] = True
        async_dispatcher_send(self.hass, SIGNAL_STATE_UPDATED)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        """Turn the switch off."""
        self._attr_is_on = False
        self.hass.data[DOMAIN]["api_extern_active"] = False
        async_dispatcher_send(self.hass, SIGNAL_STATE_UPDATED)
        self.async_write_ha_state()
