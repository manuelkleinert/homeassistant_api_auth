from homeassistant.helpers.discovery import async_load_platform

    # Load the Switch platform so a UI toggle can be presented
    await async_load_platform(hass, "switch", "api_auth", {}, config)