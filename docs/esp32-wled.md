# Individual panel control: replace the controller with an ESP32 + WLED

> **[English](esp32-wled.md) | [Deutsch](esp32-wled.de.md)**

The original Bluetooth controller only accepts one color, scene or music mode for the whole light; there is no known BLE command for individual panels. The panels themselves use addressable WS281x LEDs, though. If you replace the controller with an ESP32 running [WLED](https://kno.wled.ge/), you can give every hexagon its own color and use all WLED effects.

This guide was written by [@Nisbo](https://github.com/Nisbo) in [issue #1](https://github.com/777Timo/MeRgbW-ble-HA/issues/1#issuecomment-5061774110). Photos and measurements are theirs.

> **Note:** After the conversion the light is controlled by WLED and no longer by this integration. Home Assistant discovers WLED devices automatically through the built-in [WLED integration](https://www.home-assistant.io/integrations/wled/); you can remove the MeRgbW BLE device. Opening the device is at your own risk — disconnect power first.

---

## Device

Tested with [this hexagon set on Amazon](https://www.amazon.de/dp/B0D91W2B32): 12 panels with 7 LEDs each = **84 LEDs**.

<img width="400" alt="Original Bluetooth controller replaced with an ESP32" src="https://github.com/user-attachments/assets/2b3ffb30-7f7a-4f64-9a51-896e0c5027f7" />

### Inside one hexagon panel

Each hexagon contains seven addressable LEDs.

<img width="400" alt="Inside one hexagon panel" src="https://github.com/user-attachments/assets/fae2f92b-07a8-438b-b5a2-3af6783245f9" />

The connections between the panels are:

| Pad | Signal |
|-----|--------|
| `+` | 5 V |
| `D` | Data |
| `-` | GND |

<img width="400" alt="Hexagon panel power and data connections" src="https://github.com/user-attachments/assets/3e64d0d9-92fd-4ade-b6d8-300f9b2c277c" />

---

## Wiring

```text
+ (red)   -> 5 V
- (black) -> GND
D (white) -> GPIO 2 or GPIO 4
```

GPIO 2 is the default LED data pin in WLED; GPIO 4 works as well and can be selected in WLED.

### Power supply

Do **not** power all 84 LEDs through the ESP32 board — the current can be too high for the board, its voltage regulator or its USB connector. Connect the 5 V supply directly to the panels and the ESP32 in parallel:

```text
5 V power supply +  -> LED panels +
                    -> ESP32 5 V

5 V power supply -  -> LED panels -
                    -> ESP32 GND

ESP32 GPIO 2 or 4   -> LED panels D
```

- The ESP32 and the panels must share the same GND.
- If you reuse the original two-wire USB power cable, check the polarity with a multimeter first. In @Nisbo's cable, red was 5 V and **white was GND**.
- Do not connect the ESP32 to USB and to the external 5 V supply at the same time, unless your board is designed to prevent backfeeding.

---

## WLED configuration

**Config → LED Preferences:**

| Setting | Value |
|---------|-------|
| LED type | WS281x |
| LED count | 84 |
| GPIO | 2 or 4 |
| Color order | GRB |

## Segments: one per hexagon

The following command creates 13 segments: segment 0 covers all 84 LEDs, segments 1–12 are the individual panels (7 LEDs each). Replace `192.168.179.160` with the IP address of your WLED device. The panel names (`Panel_<column>_<row>`) describe @Nisbo's layout — rename them to match yours.

```bash
curl -X POST "http://192.168.179.160/json/state" \
  -H "Content-Type: application/json" \
  -d '{
    "mainseg": 0,
    "seg": [
      {"id": 0,  "start": 0,  "stop": 84, "n": "Gesamt",    "on": true, "sel": true},
      {"id": 1,  "start": 0,  "stop": 7,  "n": "Panel_1_1", "on": true, "sel": false},
      {"id": 2,  "start": 7,  "stop": 14, "n": "Panel_2_2", "on": true, "sel": false},
      {"id": 3,  "start": 14, "stop": 21, "n": "Panel_2_1", "on": true, "sel": false},
      {"id": 4,  "start": 21, "stop": 28, "n": "Panel_3_1", "on": true, "sel": false},
      {"id": 5,  "start": 28, "stop": 35, "n": "Panel_3_2", "on": true, "sel": false},
      {"id": 6,  "start": 35, "stop": 42, "n": "Panel_3_3", "on": true, "sel": false},
      {"id": 7,  "start": 42, "stop": 49, "n": "Panel_4_2", "on": true, "sel": false},
      {"id": 8,  "start": 49, "stop": 56, "n": "Panel_5_2", "on": true, "sel": false},
      {"id": 9,  "start": 56, "stop": 63, "n": "Panel_6_2", "on": true, "sel": false},
      {"id": 10, "start": 63, "stop": 70, "n": "Panel_6_1", "on": true, "sel": false},
      {"id": 11, "start": 70, "stop": 77, "n": "Panel_5_1", "on": true, "sel": false},
      {"id": 12, "start": 77, "stop": 84, "n": "Panel_4_1", "on": true, "sel": false}
    ]
  }'
```

### Save the layout as a preset

```bash
curl -X POST "http://192.168.179.160/json/state" \
  -H "Content-Type: application/json" \
  -d '{"psave": 1, "n": "Grundaufteilung", "sb": true}'
```

This saves the segment layout as preset `1` ("Grundaufteilung" = base layout). Select it in WLED to restore the layout, or load it automatically after startup:

```text
Config -> LED Preferences -> Apply preset at boot -> 1
```
