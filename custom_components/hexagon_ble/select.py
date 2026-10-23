"""Hexagon BLE – select entity for effect selection."""
from __future__ import annotations

import asyncio
import logging

from bleak import BleakClient
from bleak.exc import BleakError
from bleak_retry_connector import establish_connection

from homeassistant.components.bluetooth import async_ble_device_from_address
from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN, WRITE_CHAR_UUID, NOTIFY_CHAR_UUID,
    EFFECT_LOOKUP, NO_EFFECT,
    cmd_effect, effect_list, resolve_language,
)

_LOGGER = logging.getLogger(__name__)
CONNECT_TIMEOUT = 15.0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    address = entry.data["address"]
    async_add_entities([HexagonEffectSelect(hass, address, entry.title, entry.entry_id)])


class HexagonEffectSelect(SelectEntity):
    _attr_has_entity_name = True
    _attr_translation_key = "effect"
    _attr_icon = "mdi:palette"

    def __init__(self, hass: HomeAssistant, address: str, name: str, entry_id: str) -> None:
        self.hass = hass
        self._address = address
        self._lock = asyncio.Lock()
        self._attr_unique_id = f"hexagon_ble_effect_{address.replace(':', '_')}"
        self._attr_device_info = {"identifiers": {(DOMAIN, address)}, "name": name}
        language = resolve_language(hass.config.language)
        self._attr_options = [NO_EFFECT[language]] + effect_list(language)
        self._attr_current_option = NO_EFFECT[language]

    async def async_select_option(self, option: str) -> None:
        self._attr_current_option = option
        self.async_write_ha_state()

        if option not in EFFECT_LOOKUP:
            return

        await self._send(cmd_effect(*EFFECT_LOOKUP[option]))

    async def _send(self, cmd: bytes) -> None:
        async with self._lock:
            ble_device = async_ble_device_from_address(
                self.hass, self._address, connectable=True
            ) or async_ble_device_from_address(
                self.hass, self._address, connectable=False
            )
            if ble_device is None:
                _LOGGER.warning("Hexagon (%s) not reachable – out of range or connected to the MeRGBW app?", self._address)
                return
            try:
                client = await establish_connection(
                    BleakClient, ble_device, self._address, timeout=CONNECT_TIMEOUT
                )
                try:
                    try:
                        await client.start_notify(NOTIFY_CHAR_UUID, lambda s, d: None)
                    except BleakError:
                        pass
                    await asyncio.sleep(0.1)
                    _LOGGER.debug("Hexagon effect: sending %s", cmd.hex())
                    await client.write_gatt_char(WRITE_CHAR_UUID, cmd, response=False)
                finally:
                    await client.disconnect()
            except BleakError as err:
                _LOGGER.warning("BLE error for %s: %s", self._address, err)
            except asyncio.TimeoutError:
                _LOGGER.warning("BLE timeout for %s", self._address)
            except Exception as err:
                _LOGGER.warning("Unexpected error for %s: %s", self._address, err)
