#!/usr/bin/env python3
"""Analysiert Notifications der Hexagon-Lampe nach verschiedenen Befehlen."""
import asyncio

ADDRESS = "XX:XX:XX:XX:XX:XX"  # replace with your device MAC
WRITE_UUID = "0000fff3-0000-1000-8000-00805f9b34fb"
NOTIFY_UUID = "0000fff4-0000-1000-8000-00805f9b34fb"


def _cs(data: bytes) -> int:
    return (0xFF - (sum(data) & 0xFF)) & 0xFF


CMDS = {
    "ON":              bytes.fromhex("5501ff0601a3"),
    "Farbe Rot":       bytes.fromhex("5503ff09000003e8b4"),
    "Farbe Grün":      bytes.fromhex("5503ff09015e03e8" + format((0xFF - (sum(bytes.fromhex("5503ff09015e03e8")) & 0xFF)) & 0xFF, "02x")),
    "Farbe Blau":      bytes.fromhex("5503ff0900e803e8" + format((0xFF - (sum(bytes.fromhex("5503ff0900e803e8")) & 0xFF)) & 0xFF, "02x")),
    "Helligkeit 50%":  bytes(b'\x55\x05\xff\x07' + (500).to_bytes(2, 'big')) + bytes([_cs(b'\x55\x05\xff\x07' + (500).to_bytes(2, 'big'))]),
    "Szene 1":         bytes([0x55,0x06,0xFF,0x07,0x00,0x01]) + bytes([_cs(bytes([0x55,0x06,0xFF,0x07,0x00,0x01]))]),
    "Musik-Modus 1":   bytes([0x55,0x07,0xFF,0x06,0x01]) + bytes([_cs(bytes([0x55,0x07,0xFF,0x06,0x01]))]),
    "Speed 0%":        bytes([0x55,0x0F,0xFF,0x06,100]) + bytes([_cs(bytes([0x55,0x0F,0xFF,0x06,100]))]),
    "Speed 100%":      bytes([0x55,0x0F,0xFF,0x06,0]) + bytes([_cs(bytes([0x55,0x0F,0xFF,0x06,0]))]),
    "Sensitivity 50%": bytes([0x55,0x08,0xFF,0x06,50]) + bytes([_cs(bytes([0x55,0x08,0xFF,0x06,50]))]),
}

# Mögliche Query-Befehle (unbekannte Typen — nur falls Lampe antwortet)
QUERIES = {
    "Query 0x02":  bytes([0x55,0x02,0xFF,0x05]) + bytes([_cs(bytes([0x55,0x02,0xFF,0x05]))]),
    "Query 0x04":  bytes([0x55,0x04,0xFF,0x05]) + bytes([_cs(bytes([0x55,0x04,0xFF,0x05]))]),
    "Query 0x10":  bytes([0x55,0x10,0xFF,0x05]) + bytes([_cs(bytes([0x55,0x10,0xFF,0x05]))]),
    "Query 0xFF":  bytes([0x55,0xFF,0xFF,0x05]) + bytes([_cs(bytes([0x55,0xFF,0xFF,0x05]))]),
}


async def run():
    try:
        from bleak import BleakClient, BleakScanner
    except ImportError:
        print("bleak nicht installiert: pip install bleak")
        return

    print(f"Suche {ADDRESS} ...")
    device = await BleakScanner.find_device_by_address(ADDRESS, timeout=15)
    if not device:
        # macOS: per Name suchen
        devices = await BleakScanner.discover(timeout=10, return_adv=True)
        for d, adv in devices.values():
            if "hexagon" in (d.name or "").lower() or ADDRESS.lower() in str(d.address).lower():
                device = d
                break
    if not device:
        print("Gerät nicht gefunden — MeRGBW-App trennen und erneut versuchen.")
        return
    print(f"Gefunden: {device.name} ({device.address})")

    notifications: list[tuple[str, bytes]] = []
    current_label = ""

    async with BleakClient(device) as client:
        print(f"Verbunden\n")

        def notify_cb(sender, data):
            print(f"  <<< NOTIFY [{current_label}]: {data.hex()}  ({list(data)})")
            notifications.append((current_label, data))

        try:
            await client.start_notify(NOTIFY_UUID, notify_cb)
        except Exception as e:
            print(f"start_notify fehlgeschlagen: {e}")

        # Kurz lauschen ob Lampe spontan etwas sendet
        print("--- Lausche 2s ohne Befehl ---")
        current_label = "spontan"
        await asyncio.sleep(2.0)

        # Bekannte Befehle testen
        print("\n--- Bekannte Befehle ---")
        for label, cmd in CMDS.items():
            current_label = label
            print(f"\nSende [{label}]: {cmd.hex()}")
            await client.write_gatt_char(WRITE_UUID, cmd, response=False)
            await asyncio.sleep(1.5)

        # Query-Befehle testen
        print("\n--- Query-Befehle (unbekannte Typen) ---")
        for label, cmd in QUERIES.items():
            current_label = label
            print(f"\nSende [{label}]: {cmd.hex()}")
            await client.write_gatt_char(WRITE_UUID, cmd, response=False)
            await asyncio.sleep(1.5)

    # Auswertung
    print("\n" + "="*60)
    print("ZUSAMMENFASSUNG aller Notifications:")
    print("="*60)
    if not notifications:
        print("Keine Notifications empfangen.")
    else:
        for label, data in notifications:
            print(f"  [{label:25s}] {data.hex()}  len={len(data)}")

asyncio.run(run())
