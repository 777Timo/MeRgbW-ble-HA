"""Hexagon BLE Light entity."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from bleak import BleakClient
from bleak.exc import BleakError
from bleak_retry_connector import establish_connection

from homeassistant.components.bluetooth import async_ble_device_from_address
from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_EFFECT,
    ATTR_RGB_COLOR,
    ColorMode,
    LightEntity,
    LightEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CMD_OFF,
    CMD_ON,
    DOMAIN,
    EFFECT_LOOKUP,
    NOTIFY_CHAR_UUID,
    WRITE_CHAR_UUID,
    cmd_brightness,
    cmd_color,
    cmd_effect,
    effect_list,
    effect_name,
    resolve_language,
)

_LOGGER = logging.getLogger(__name__)

CONNECT_TIMEOUT = 15.0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    address = entry.data["address"]
    async_add_entities([HexagonBLELight(hass, address, entry.title, entry.entry_id)])


class HexagonBLELight(LightEntity):
    _attr_color_mode = ColorMode.RGB
    _attr_supported_color_modes = {ColorMode.RGB}
    _attr_supported_features = LightEntityFeature.EFFECT
    _attr_has_entity_name = True
    _attr_name = None

    def __init__(self, hass: HomeAssistant, address: str, name: str, entry_id: str) -> None:
        self.hass = hass
        self._address = address
        self._language = resolve_language(hass.config.language)
        self._attr_effect_list = effect_list(self._language)
        self._attr_unique_id = f"hexagon_ble_{address.replace(':', '_')}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, address)},
            "name": name,
            "model": "Hexagon BLE",
            "manufacturer": "MeRGBW",
        }
        self._is_on: bool = False
        self._brightness: int = 255
        self._rgb: tuple[int, int, int] = (255, 255, 255)
        self._effect: str | None = None
        self._lock = asyncio.Lock()

    @property
    def is_on(self) -> bool:
        return self._is_on

    @property
    def brightness(self) -> int:
        return self._brightness

    @property
    def rgb_color(self) -> tuple[int, int, int]:
        return self._rgb

    @property
    def effect(self) -> str | None:
        return self._effect

    async def async_turn_on(self, **kwargs: Any) -> None:
        commands: list[bytes] = []

        if not self._is_on:
            commands.append(CMD_ON)

        if ATTR_EFFECT in kwargs:
            effect = kwargs[ATTR_EFFECT]
            if effect in EFFECT_LOOKUP:
                kind, index = EFFECT_LOOKUP[effect]
                self._effect = effect_name(self._language, kind, index)
                commands.append(cmd_effect(kind, index))
            else:
                _LOGGER.warning("Hexagon (%s): unknown effect %r", self._address, effect)
        else:
            if ATTR_RGB_COLOR in kwargs:
                self._rgb = kwargs[ATTR_RGB_COLOR]
                self._effect = None
                commands.append(cmd_color(*self._rgb))

            if ATTR_BRIGHTNESS in kwargs:
                self._brightness = kwargs[ATTR_BRIGHTNESS]
                commands.append(cmd_brightness(self._brightness))

        if not commands:
            commands.append(CMD_ON)

        self._is_on = True
        self.async_write_ha_state()
        await self._send_commands(commands)

    async def async_turn_off(self, **kwargs: Any) -> None:
        self._is_on = False
        self.async_write_ha_state()
        await self._send_commands([CMD_OFF])

    async def _send_commands(self, commands: list[bytes]) -> None:
        async with self._lock:
            ble_device = async_ble_device_from_address(
                self.hass, self._address, connectable=True
            ) or async_ble_device_from_address(
                self.hass, self._address, connectable=False
            )
            if ble_device is None:
                _LOGGER.warning(
                    "Hexagon (%s) not reachable – out of range or connected to the MeRGBW app?",
                    self._address,
                )
                return

            try:
                client = await establish_connection(
                    BleakClient, ble_device, self._address, timeout=CONNECT_TIMEOUT
                )
                try:
                    def _notify_handler(sender, data):
                        _LOGGER.debug("Notify from %s: %s", sender, data.hex())
                    try:
                        await client.start_notify(NOTIFY_CHAR_UUID, _notify_handler)
                    except BleakError:
                        pass
                    await asyncio.sleep(0.1)
                    for cmd in commands:
                        _LOGGER.debug("Hexagon: sending %s", cmd.hex())
                        await client.write_gatt_char(WRITE_CHAR_UUID, cmd, response=False)
                        await asyncio.sleep(0.05)
                finally:
                    await client.disconnect()
            except BleakError as err:
                _LOGGER.warning("BLE error for %s: %s", self._address, err)
            except asyncio.TimeoutError:
                _LOGGER.warning("BLE timeout for %s", self._address)
            except Exception as err:
                _LOGGER.warning("Unexpected error for %s: %s", self._address, err)
