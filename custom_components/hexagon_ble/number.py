"""Hexagon BLE – Number-Entities für Geschwindigkeit und Empfindlichkeit."""
from __future__ import annotations

import asyncio
import logging

from bleak import BleakClient
from bleak.exc import BleakError
from bleak_retry_connector import establish_connection

from homeassistant.components.bluetooth import async_ble_device_from_address
from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, WRITE_CHAR_UUID, NOTIFY_CHAR_UUID, cmd_scene_speed, cmd_music_sensitivity

_LOGGER = logging.getLogger(__name__)

CONNECT_TIMEOUT = 15.0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    address = entry.data["address"]
    async_add_entities([
        HexagonSpeedNumber(hass, address, entry.entry_id),
        HexagonSensitivityNumber(hass, address, entry.entry_id),
    ])


class HexagonBLENumberBase(NumberEntity):
    _attr_has_entity_name = True
    _attr_mode = NumberMode.SLIDER
    _attr_native_min_value = 0.0
    _attr_native_max_value = 100.0
    _attr_native_step = 1.0
    _attr_native_unit_of_measurement = "%"

    def __init__(self, hass: HomeAssistant, address: str, entry_id: str) -> None:
        self.hass = hass
        self._address = address
        self._lock = asyncio.Lock()
        self._attr_device_info = {"identifiers": {(DOMAIN, address)}}

    async def async_set_native_value(self, value: float) -> None:
        self._attr_native_value = value
        self.async_write_ha_state()
        await self._send(self._build_command(int(value)))

    def _build_command(self, value: int) -> bytes:
        raise NotImplementedError

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
                    await client.write_gatt_char(WRITE_CHAR_UUID, cmd, response=False)
                finally:
                    await client.disconnect()
            except BleakError as err:
                _LOGGER.warning("BLE-Fehler für %s: %s", self._address, err)
            except asyncio.TimeoutError:
                _LOGGER.warning("BLE-Timeout für %s", self._address)
            except Exception as err:
                _LOGGER.warning("Unerwarteter Fehler für %s: %s", self._address, err)


class HexagonSpeedNumber(HexagonBLENumberBase):
    _attr_name = "Animationsgeschwindigkeit"
    _attr_icon = "mdi:speedometer"
    _attr_native_value = 50.0

    def __init__(self, hass: HomeAssistant, address: str, entry_id: str) -> None:
        super().__init__(hass, address, entry_id)
        self._attr_unique_id = f"hexagon_ble_speed_{address.replace(':', '_')}"

    def _build_command(self, value: int) -> bytes:
        return cmd_scene_speed(value)


class HexagonSensitivityNumber(HexagonBLENumberBase):
    _attr_name = "Musikempfindlichkeit"
    _attr_icon = "mdi:microphone"
    _attr_native_value = 50.0

    def __init__(self, hass: HomeAssistant, address: str, entry_id: str) -> None:
        super().__init__(hass, address, entry_id)
        self._attr_unique_id = f"hexagon_ble_sensitivity_{address.replace(':', '_')}"

    def _build_command(self, value: int) -> bytes:
        return cmd_music_sensitivity(value)
