"""Config flow for Hexagon BLE Lights."""
from __future__ import annotations

import voluptuous as vol
from homeassistant.components.bluetooth import BluetoothServiceInfoBleak
from homeassistant.config_entries import ConfigFlow
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN


class HexagonBLEConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._discovery_info: BluetoothServiceInfoBleak | None = None
        self._address: str | None = None

    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfoBleak
    ) -> FlowResult:
        """Handle Bluetooth discovery."""
        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()

        self._discovery_info = discovery_info
        self._address = discovery_info.address
        self.context["title_placeholders"] = {"name": discovery_info.name or "MeRgbW BLE"}
        return await self.async_step_confirm()

    async def async_step_confirm(self, user_input=None) -> FlowResult:
        """Confirm discovered device."""
        if user_input is not None:
            return self.async_create_entry(
                title=self._discovery_info.name or "MeRgbW BLE",
                data={"address": self._address},
            )

        return self.async_show_form(
            step_id="confirm",
            description_placeholders={
                "name": self._discovery_info.name or "Hexagon Lights",
                "address": self._address,
            },
        )

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Manual setup by MAC address."""
        errors: dict[str, str] = {}

        if user_input is not None:
            address = user_input["address"].upper()
            await self.async_set_unique_id(address)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=user_input.get("name", "MeRgbW BLE"),
                data={"address": address},
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("address"): str,
                    vol.Optional("name", default="MeRgbW BLE"): str,
                }
            ),
            errors=errors,
        )
