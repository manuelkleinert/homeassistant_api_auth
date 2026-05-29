import logging
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.event import async_track_state_change_event

_LOGGER = logging.getLogger(__name__)

DOMAIN = "api_auth"

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the sensor platform from a config entry."""
    async_add_entities([WebsiteApiLastActionSensor(hass)])
    return True


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the sensor platform (legacy)."""
    async_add_entities([WebsiteApiLastActionSensor(hass)])
    return True


class WebsiteApiLastActionSensor(SensorEntity, RestoreEntity):
    """Sensor showing the last action of the Website API."""

    def __init__(self, hass):
        self.hass = hass
        self._attr_name = "Webseite API Log"
        self._attr_unique_id = "website_api_log"
        self._attr_icon = "mdi:history"
        self._state = None
        self._extra_state_attributes = {}
        
        # Ensure the entity ID is exactly what the external script targets
        self.entity_id = "sensor.website_api_log"

    async def async_added_to_hass(self) -> None:
        """Handle when entity is added."""
        await super().async_added_to_hass()
        
        # Restore the last state and attributes from HA storage
        last_state = await self.async_get_last_state()
        if last_state:
            self._state = last_state.state
            # friendly_name and icon are built-in attributes, skip them to prevent duplicates in extra attributes
            attrs = dict(last_state.attributes)
            attrs.pop("friendly_name", None)
            attrs.pop("icon", None)
            self._extra_state_attributes = attrs

        # Listen to state change events to stay in sync when the state is updated externally (e.g. via REST API)
        self.async_on_remove(
            async_track_state_change_event(
                self.hass, [self.entity_id], self._async_state_changed_listener
            )
        )

    async def _async_state_changed_listener(self, event) -> None:
        """Handle state change events for this entity."""
        new_state = event.data.get("new_state")
        if new_state:
            self._state = new_state.state
            attrs = dict(new_state.attributes)
            attrs.pop("friendly_name", None)
            attrs.pop("icon", None)
            self._extra_state_attributes = attrs

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return self._extra_state_attributes
