#!/usr/bin/env python3
"""Scannt alle Typ-Bytes 0x00–0xFF auf Query-Antworten der Hexagon-Lampe."""
import asyncio

ADDRESS = "XX:XX:XX:XX:XX:XX"  # replace with your device MAC
WRITE_UUID = "0000fff3-0000-1000-8000-00805f9b34fb"
NOTIFY_UUID = "0000fff4-0000-1000-8000-00805f9b34fb"

# Standard-ACK-Muster — alles was davon abweicht ist interessant
STANDARD_ACK = {6}  # len=6 ist normales ACK

def _cs(data: bytes) -> int:
    return (0xFF - (sum(data) & 0xFF)) & 0xFF

def make_query(type_byte: int) -> bytes:
    p = bytes([0x55, type_byte, 0xFF, 0x05])
    return p + bytes([_cs(p)])


async def run():
    try:
        from bleak import BleakClient, BleakScanner
    except ImportError:
        print("bleak nicht installiert: pip install bleak")
        return

    print(f"Suche {ADDRESS} ...")
    device = await BleakScanner.find_device_by_address(ADDRESS, timeout=15)
    if not device:
        devices = await BleakScanner.discover(timeout=10, return_adv=True)
        for d, adv in devices.values():
            if "hexagon" in (d.name or "").lower():
                device = d
                break
    if not device:
        print("Gerät nicht gefunden.")
        return
    print(f"Gefunden: {device.name} ({device.address})\n")

    interesting: list[tuple[int, bytes]] = []
    last_notify: list[bytes] = []

    async with BleakClient(device) as client:
        # Zuerst ON senden
        on_cmd = bytes.fromhex("5501ff0601a3")
        await client.write_gatt_char(WRITE_UUID, on_cmd, response=False)
        await asyncio.sleep(0.5)

        def notify_cb(sender, data):
            last_notify.clear()
            last_notify.append(data)

        await client.start_notify(NOTIFY_UUID, notify_cb)
        await asyncio.sleep(0.2)

        for t in range(0x00, 0x100):
            last_notify.clear()
            cmd = make_query(t)
            try:
                await client.write_gatt_char(WRITE_UUID, cmd, response=False)
            except Exception:
                continue
            await asyncio.sleep(0.15)

            if last_notify:
                data = last_notify[0]
                is_std_ack = (len(data) == 6 and data[4] == 0x00)
                marker = "   " if is_std_ack else ">>>"
                print(f"{marker} 0x{t:02X}: {data.hex()}  len={len(data)}")
                if not is_std_ack:
                    interesting.append((t, data))
            # kein Output für keine Antwort

    print("\n" + "="*60)
    print("INTERESSANTE ANTWORTEN (nicht Standard-ACK):")
    print("="*60)
    if not interesting:
        print("Keine gefunden — alle Antworten sind Standard-ACKs.")
    else:
        for t, data in interesting:
            print(f"  0x{t:02X}: {data.hex()}  len={len(data)}  bytes={list(data)}")

asyncio.run(run())
