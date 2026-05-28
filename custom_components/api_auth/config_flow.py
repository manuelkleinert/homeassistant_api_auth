from homeassistant import config_entries
from homeassistant.core import callback
import voluptuous as vol

DOMAIN = "api_auth"

class ApiAuthConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for API Auth."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            return self.async_create_entry(title="API Auth", data={})

        return self.async_show_form(step_id="user")

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return ApiAuthOptionsFlowHandler(config_entry)


class ApiAuthOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for API Auth user management."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self._config_entry = config_entry
        self._selected_user = None

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        return await self.async_step_menu()

    async def async_step_menu(self, user_input=None):
        """Show the management menu."""
        if user_input is not None:
            action = user_input.get("action")
            if action == "add_user":
                return await self.async_step_add_user()
            if action == "change_password":
                return await self.async_step_select_user_password()
            if action == "delete_user":
                return await self.async_step_select_user_delete()

        return self.async_show_form(
            step_id="menu",
            data_schema=vol.Schema({
                vol.Required("action"): vol.In({
                    "add_user": "Benutzer hinzufügen",
                    "change_password": "Passwort ändern",
                    "delete_user": "Benutzer löschen"
                })
            })
        )

    async def async_step_add_user(self, user_input=None):
        """Step to add a new user."""
        errors = {}
        if user_input is not None:
            storage = self.hass.data[DOMAIN]["storage"]
            success = await self.hass.async_add_executor_job(
                storage.add_user, 
                user_input["username"], 
                user_input["password"], 
                user_input.get("role", "user")
            )
            if success:
                return self.async_create_entry(title="", data={})
            errors["base"] = "user_exists"

        return self.async_show_form(
            step_id="add_user",
            data_schema=vol.Schema({
                vol.Required("username"): str,
                vol.Required("password"): str,
                vol.Optional("role", default="user"): str,
            }),
            errors=errors
        )

    async def async_step_select_user_password(self, user_input=None):
        """Step to select user for password change."""
        if user_input is not None:
            self._selected_user = user_input["username"]
            return await self.async_step_change_password()

        storage = self.hass.data[DOMAIN]["storage"]
        users = await self.hass.async_add_executor_job(storage.get_users)
        
        return self.async_show_form(
            step_id="select_user_password",
            data_schema=vol.Schema({
                vol.Required("username"): vol.In(users)
            })
        )

    async def async_step_change_password(self, user_input=None):
        """Step to change password."""
        if user_input is not None:
            storage = self.hass.data[DOMAIN]["storage"]
            await self.hass.async_add_executor_job(
                storage.update_password, self._selected_user, user_input["new_password"]
            )
            return self.async_create_entry(title="", data={})

        return self.async_show_form(
            step_id="change_password",
            data_schema=vol.Schema({
                vol.Required("new_password"): str,
            }),
            description_placeholders={"username": self._selected_user}
        )

    async def async_step_select_user_delete(self, user_input=None):
        """Step to select user for deletion."""
        if user_input is not None:
            storage = self.hass.data[DOMAIN]["storage"]
            await self.hass.async_add_executor_job(
                storage.delete_user, user_input["username"]
            )
            return self.async_create_entry(title="", data={})

        storage = self.hass.data[DOMAIN]["storage"]
        users = await self.hass.async_add_executor_job(storage.get_users)
        
        return self.async_show_form(
            step_id="select_user_delete",
            data_schema=vol.Schema({
                vol.Required("username"): vol.In(users)
            })
        )
