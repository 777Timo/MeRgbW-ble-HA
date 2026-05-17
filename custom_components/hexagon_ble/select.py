"""Hexagon BLE – Select-Entity für Effekt-Auswahl."""
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
    EFFECT_LIST, SCENE_INDEX, MUSIC_INDEX,
    cmd_scene, cmd_music_mode,
)

_LOGGER = logging.getLogger(__name__)
CONNECT_TIMEOUT = 15.0
NO_EFFECT = "Kein Effekt (Farbe)"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    address = entry.data["address"]
    async_add_entities([HexagonEffectSelect(hass, address, entry.title, entry.entry_id)])


class HexagonEffectSelect(SelectEntity):
    _attr_has_entity_name = True
    _attr_name = "Effekt"
    _attr_icon = "mdi:palette"

    def __init__(self, hass: HomeAssistant, address: str, name: str, entry_id: str) -> None:
        self.hass = hass
        self._address = address
        self._lock = asyncio.Lock()
        self._attr_unique_id = f"hexagon_ble_effect_{address.replace(':', '_')}"
        self._attr_device_info = {"identifiers": {(DOMAIN, address)}, "name": name}
        self._attr_options = [NO_EFFECT] + EFFECT_LIST
        self._attr_current_option = NO_EFFECT

    async def async_select_option(self, option: str) -> None:
        self._attr_current_option = option
        self.async_write_ha_state()

        if option == NO_EFFECT:
            return

        if option in SCENE_INDEX:
            cmd = cmd_scene(SCENE_INDEX[option])
        elif option in MUSIC_INDEX:
            cmd = cmd_music_mode(MUSIC_INDEX[option])
        else:
            return

        await self._send(cmd)

    async def _send(self, cmd: bytes) -> None:
        async with self._lock:
            ble_device = async_ble_device_from_address(
                self.hass, self._address, connectable=True
            ) or async_ble_device_from_address(
                self.hass, self._address, connectable=False
            )
            if ble_device is None:
                _LOGGER.warning("Hexagon (%s) nicht erreichbar", self._address)
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
                    _LOGGER.warning("Hexagon Effekt: Sende %s", cmd.hex())
                    await client.write_gatt_char(WRITE_CHAR_UUID, cmd, response=False)
                finally:
                    await client.disconnect()
            except BleakError as err:
                _LOGGER.warning("BLE-Fehler für %s: %s", self._address, err)
            except asyncio.TimeoutError:
                _LOGGER.warning("BLE-Timeout für %s", self._address)
            except Exception as err:
                _LOGGER.warning("Unerwarteter Fehler für %s: %s", self._address, err)
