import logging
from homeassistant.components.select import SelectEntity
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.dispatcher import async_dispatcher_connect, async_dispatcher_send

_LOGGER = logging.getLogger(__name__)

DOMAIN = "api_auth"
SIGNAL_STATE_UPDATED = f"{DOMAIN}_state_updated"

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the select platform from a config entry."""
    async_add_entities([ApiExternPageSelect(hass)])
    return True


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the select platform (legacy)."""
    async_add_entities([ApiExternPageSelect(hass)])
    return True


class ApiExternPageSelect(SelectEntity, RestoreEntity):
    """Custom Select entity with internal state persistence."""

    def __init__(self, hass):
        self.hass = hass
        self._attr_name = "API Extern Page (Select)"
        self._attr_unique_id = "api_extern_page_select"
        self._attr_options = ["true", "false"]
        self._attr_current_option = "false"

    async def async_added_to_hass(self) -> None:
        """Handle when entity is added."""
        await super().async_added_to_hass()
        
        # Restore last state
        last_state = await self.async_get_last_state()
        if last_state:
            self._attr_current_option = last_state.state
            self.hass.data[DOMAIN]["api_extern_active"] = (last_state.state == "true")

        # Listen for updates from the switch
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, SIGNAL_STATE_UPDATED, self._update_state
            )
        )

    async def _update_state(self) -> None:
        """Update state when notified by dispatcher."""
        flag = self.hass.data[DOMAIN].get("api_extern_active", False)
        self._attr_current_option = "true" if flag else "false"
        self.async_write_ha_state()

    @property
    def current_option(self) -> str:
        return self._attr_current_option

    async def async_select_option(self, option: str) -> None:
        """Handle a user selecting an option."""
        if option not in self._attr_options:
            return
            
        self._attr_current_option = option
        self.hass.data[DOMAIN]["api_extern_active"] = (option == "true")
        
        # Notify switch
        async_dispatcher_send(self.hass, SIGNAL_STATE_UPDATED)
        self.async_write_ha_state()
