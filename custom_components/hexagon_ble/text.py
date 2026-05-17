"""Hexagon BLE – Text-Entity zum manuellen Testen von Hex-Befehlen."""
from __future__ import annotations

import asyncio
import logging

from bleak import BleakClient
from bleak.exc import BleakError
from bleak_retry_connector import establish_connection

from homeassistant.components.bluetooth import async_ble_device_from_address
from homeassistant.components.text import TextEntity, TextMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, WRITE_CHAR_UUID, NOTIFY_CHAR_UUID

_LOGGER = logging.getLogger(__name__)

CONNECT_TIMEOUT = 15.0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    address = entry.data["address"]
    async_add_entities([HexagonBLEDebugText(hass, address, entry.entry_id)])


class HexagonBLEDebugText(TextEntity):
    _attr_has_entity_name = True
    _attr_name = "BLE Debug Command"
    _attr_mode = TextMode.TEXT
    _attr_native_min = 0
    _attr_native_max = 128
    _attr_pattern = r"^[0-9a-fA-F ]*$"
    _attr_icon = "mdi:console"
    _attr_native_value = ""

    def __init__(self, hass: HomeAssistant, address: str, entry_id: str) -> None:
        self.hass = hass
        self._address = address
        self._attr_unique_id = f"hexagon_ble_debug_{address.replace(':', '_')}"
        self._attr_device_info = {"identifiers": {(DOMAIN, address)}}
        self._lock = asyncio.Lock()

    async def async_set_value(self, value: str) -> None:
        value = value.strip().replace(" ", "")
        if not value:
            self._attr_native_value = ""
            self.async_write_ha_state()
            return
        if len(value) % 2 != 0:
            _LOGGER.warning("Hexagon Debug: ungerade Hex-Länge ignoriert: %s", value)
            return
        try:
            cmd = bytes.fromhex(value)
        except ValueError:
            _LOGGER.warning("Hexagon Debug: ungültiges Hex ignoriert: %s", value)
            return

        self._attr_native_value = value
        self.async_write_ha_state()
        _LOGGER.warning("Hexagon Debug: Sende %s (%d Bytes)", value, len(cmd))
        await self._send(cmd)

    async def _send(self, cmd: bytes) -> None:
        async with self._lock:
            ble_device = async_ble_device_from_address(
                self.hass, self._address, connectable=True
            ) or async_ble_device_from_address(
                self.hass, self._address, connectable=False
            )
            if ble_device is None:
                _LOGGER.warning("Hexagon Debug: Gerät %s nicht erreichbar", self._address)
                return
            try:
                client = await establish_connection(
                    BleakClient, ble_device, self._address, timeout=CONNECT_TIMEOUT
                )
                try:
                    def _notify(sender, data):
                        _LOGGER.warning("Hexagon Debug NOTIFY: %s", data.hex())
                    try:
                        await client.start_notify(NOTIFY_CHAR_UUID, _notify)
                    except BleakError:
                        pass
                    await asyncio.sleep(0.1)
                    await client.write_gatt_char(WRITE_CHAR_UUID, cmd, response=False)
                    _LOGGER.warning("Hexagon Debug: OK")
                finally:
                    await client.disconnect()
            except BleakError as err:
                _LOGGER.warning("Hexagon Debug BLE-Fehler: %s", err)
            except asyncio.TimeoutError:
                _LOGGER.warning("Hexagon Debug: Timeout")
            except Exception as err:
                _LOGGER.warning("Hexagon Debug Fehler (%s): %s", type(err).__name__, err)
