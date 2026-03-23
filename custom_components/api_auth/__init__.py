from .api import AuthView, TokenCheckView, LogoutView

async def async_setup(hass, config):
    hass.http.register_view(AuthView)
    hass.http.register_view(TokenCheckView)
    hass.http.register_view(LogoutView)
    return True