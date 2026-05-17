#!/usr/bin/env python3
"""Testet Speed/Sensitivity-Befehle an der Hexagon-Lampe."""
import asyncio
import colorsys

ADDRESS = "41:42:05:1B:16:8B"
WRITE_UUID = "0000fff3-0000-1000-8000-00805f9b34fb"
NOTIFY_UUID = "0000fff4-0000-1000-8000-00805f9b34fb"


def _cs(data: bytes) -> int:
    return (0xFF - (sum(data) & 0xFF)) & 0xFF


def cmd_on() -> bytes:
    return bytes.fromhex("5501ff0601a3")


def cmd_scene(index: int) -> bytes:
    p = bytes([0x55, 0x06, 0xFF, 0x07, (index >> 8) & 0xFF, index & 0xFF])
    return p + bytes([_cs(p)])


def cmd_scene_speed(speed_pct: int) -> bytes:
    s = max(0, min(100, speed_pct))
    p = bytes([0x55, 0x0F, 0xFF, 0x07, s, 0x00])
    return p + bytes([_cs(p)])


def cmd_music_mode(index: int) -> bytes:
    p = bytes([0x55, 0x07, 0xFF, 0x06, index])
    return p + bytes([_cs(p)])


def cmd_music_sensitivity(val: int) -> bytes:
    v = max(0, min(100, val))
    p = bytes([0x55, 0x08, 0xFF, 0x06, v])
    return p + bytes([_cs(p)])


TESTS = [
    # Erst ON + Szene aktivieren
    ("ON",                          cmd_on()),
    ("Szene 1 (Zyklus)",            cmd_scene(1)),
    # Speed-Test: 0%, 50%, 100%
    ("Speed 0%",                    cmd_scene_speed(0)),
    ("Speed 50%",                   cmd_scene_speed(50)),
    ("Speed 100%",                  cmd_scene_speed(100)),
    ("Speed 50% (zurück)",          cmd_scene_speed(50)),
    # Musik-Modus testen
    ("Musik-Modus 1",               cmd_music_mode(1)),
    ("Sensitivity 0%",              cmd_music_sensitivity(0)),
    ("Sensitivity 50%",             cmd_music_sensitivity(50)),
    ("Sensitivity 100%",            cmd_music_sensitivity(100)),
]


async def test():
    try:
        from bleak import BleakClient, BleakScanner
    except ImportError:
        print("bleak nicht installiert: pip install bleak")
        return

    print(f"Suche {ADDRESS} ...")
    device = await BleakScanner.find_device_by_address(ADDRESS, timeout=15)
    if not device:
        print("Gerät nicht gefunden — MeRGBW-App trennen und erneut versuchen.")
        return
    print(f"Gefunden: {device.name}")

    async with BleakClient(device) as client:
        print(f"Verbunden: {client.is_connected}")

        def notify_cb(sender, data):
            print(f"  >>> NOTIFY: {data.hex()}")

        try:
            await client.start_notify(NOTIFY_UUID, notify_cb)
        except Exception:
            pass

        await asyncio.sleep(0.3)

        for name, cmd in TESTS:
            print(f"\nSende [{name}]: {cmd.hex()}")
            try:
                await client.write_gatt_char(WRITE_UUID, cmd, response=False)
                print("  OK")
            except Exception as e:
                print(f"  FEHLER: {e}")
            await asyncio.sleep(2.0)

        print("\nFertig.")

asyncio.run(test())
