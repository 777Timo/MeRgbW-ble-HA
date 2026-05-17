#!/usr/bin/env python3
"""Decodiert die State-Antwort (Type 0x00) unter verschiedenen Lampenzuständen."""
import asyncio

ADDRESS = "41:42:05:1B:16:8B"
WRITE_UUID = "0000fff3-0000-1000-8000-00805f9b34fb"
NOTIFY_UUID = "0000fff4-0000-1000-8000-00805f9b34fb"

def _cs(data: bytes) -> int:
    return (0xFF - (sum(data) & 0xFF)) & 0xFF

QUERY_STATE = bytes([0x55, 0x00, 0xFF, 0x05]) + bytes([_cs(bytes([0x55, 0x00, 0xFF, 0x05]))])

CMD_ON  = bytes.fromhex("5501ff0601a3")
CMD_OFF = bytes.fromhex("5501ff0600a4")

def cmd_brightness(pct: int) -> bytes:
    val = round(pct / 100 * 1000)
    p = bytes([0x55, 0x05, 0xFF, 0x07, (val >> 8) & 0xFF, val & 0xFF])
    return p + bytes([_cs(p)])

def cmd_color_hsv(hue_deg: int, sat_pct: int) -> bytes:
    sat = round(sat_pct / 100 * 1000)
    p = bytes([0x55, 0x03, 0xFF, 0x09, (hue_deg >> 8) & 0xFF, hue_deg & 0xFF,
               (sat >> 8) & 0xFF, sat & 0xFF])
    return p + bytes([_cs(p)])

def cmd_scene(index: int) -> bytes:
    p = bytes([0x55, 0x06, 0xFF, 0x07, (index >> 8) & 0xFF, index & 0xFF])
    return p + bytes([_cs(p)])


def parse_state(data: bytes) -> str:
    if len(data) < 6:
        return f"zu kurz: {data.hex()}"
    payload = data[3:-1]  # zwischen FF und checksum
    parts = [f"raw={data.hex()}", f"payload={payload.hex()}"]
    for i, b in enumerate(payload):
        parts.append(f"[{i}]={b}(0x{b:02X})")
    return "  ".join(parts)


TESTS = [
    ("ON",              [CMD_ON]),
    ("Helligkeit 25%",  [cmd_brightness(25)]),
    ("Helligkeit 50%",  [cmd_brightness(50)]),
    ("Helligkeit 100%", [cmd_brightness(100)]),
    ("Farbe Rot",       [cmd_color_hsv(0, 100)]),
    ("Farbe Grün",      [cmd_color_hsv(120, 100)]),
    ("Farbe Blau",      [cmd_color_hsv(240, 100)]),
    ("Farbe Weiß",      [cmd_color_hsv(0, 0)]),
    ("Szene 1",         [cmd_scene(1)]),
    ("Szene 5",         [cmd_scene(5)]),
    ("OFF",             [CMD_OFF]),
]


async def run():
    try:
        from bleak import BleakClient, BleakScanner
    except ImportError:
        print("bleak nicht installiert")
        return

    print(f"Suche {ADDRESS} ...")
    device = await BleakScanner.find_device_by_address(ADDRESS, timeout=15)
    if not device:
        devices = await BleakScanner.discover(timeout=10, return_adv=True)
        for d, _ in devices.values():
            if "hexagon" in (d.name or "").lower():
                device = d
                break
    if not device:
        print("Gerät nicht gefunden.")
        return

    results: list[tuple[str, bytes]] = []
    last_notify: list[bytes] = []

    async with BleakClient(device) as client:
        def notify_cb(sender, data):
            last_notify.clear()
            last_notify.append(data)

        await client.start_notify(NOTIFY_UUID, notify_cb)

        for label, cmds in TESTS:
            # Befehl(e) senden
            for cmd in cmds:
                await client.write_gatt_char(WRITE_UUID, cmd, response=False)
                await asyncio.sleep(0.3)

            # State abfragen
            last_notify.clear()
            await client.write_gatt_char(WRITE_UUID, QUERY_STATE, response=False)
            await asyncio.sleep(0.3)

            state = last_notify[0] if last_notify else b""
            results.append((label, state))
            print(f"\n[{label}]")
            if state:
                print(f"  {parse_state(state)}")
            else:
                print("  keine Antwort")

    print("\n" + "="*70)
    print("VERGLEICH (nur payload-Bytes, ohne Header/Checksum):")
    print("="*70)
    print(f"{'Zustand':<20} {'[0]':>4} {'[1]':>4} {'[2]':>5} {'[3]':>4} {'[4]':>4} {'[5]':>4} {'[6]':>4}  rest")
    print("-"*70)
    for label, data in results:
        if len(data) >= 5:
            payload = data[3:-1]
            rest = data[3+7:-1].hex() if len(payload) > 7 else ""
            cols = [f"{payload[i]:>4}" if i < len(payload) else "   -" for i in range(7)]
            print(f"{label:<20} {'  '.join(cols)}  {rest}")

asyncio.run(run())
