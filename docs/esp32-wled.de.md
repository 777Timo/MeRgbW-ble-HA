# Jedes Panel einzeln steuern: Controller durch ESP32 + WLED ersetzen

> **[English](esp32-wled.md) | [Deutsch](esp32-wled.de.md)**

Der Original-Bluetooth-Controller nimmt nur eine Farbe, Szene oder einen Musikmodus für die ganze Leuchte an; ein BLE-Befehl für einzelne Panels ist nicht bekannt. Die Panels selbst haben aber adressierbare WS281x-LEDs. Ersetzt man den Controller durch einen ESP32 mit [WLED](https://kno.wled.ge/), bekommt jedes Hexagon eine eigene Farbe, und alle WLED-Effekte stehen zur Verfügung.

Die Anleitung stammt von [@Nisbo](https://github.com/Nisbo) aus [Issue #1](https://github.com/777Timo/MeRgbW-ble-HA/issues/1#issuecomment-5061774110), ebenso die Fotos und Messwerte.

> **Hinweis:** Nach dem Umbau steuert WLED die Leuchte, nicht mehr diese Integration. Home Assistant findet WLED-Geräte automatisch über die eingebaute [WLED-Integration](https://www.home-assistant.io/integrations/wled/); das MeRgbW-BLE-Gerät kann entfernt werden. Das Öffnen des Geräts geschieht auf eigene Gefahr – vorher vom Strom trennen.

---

## Gerät

Getestet mit [diesem Hexagon-Set bei Amazon](https://www.amazon.de/dp/B0D91W2B32): 12 Panels mit je 7 LEDs = **84 LEDs**.

<img width="400" alt="Original-Bluetooth-Controller durch ESP32 ersetzt" src="https://github.com/user-attachments/assets/2b3ffb30-7f7a-4f64-9a51-896e0c5027f7" />

### Innenleben eines Panels

Jedes Hexagon enthält sieben adressierbare LEDs.

<img width="400" alt="Innenleben eines Hexagon-Panels" src="https://github.com/user-attachments/assets/fae2f92b-07a8-438b-b5a2-3af6783245f9" />

Verbindungen zwischen den Panels:

| Kontakt | Signal |
|---------|--------|
| `+` | 5 V |
| `D` | Daten |
| `-` | GND |

<img width="400" alt="Strom- und Datenanschlüsse der Panels" src="https://github.com/user-attachments/assets/3e64d0d9-92fd-4ade-b6d8-300f9b2c277c" />

---

## Verkabelung

```text
+ (rot)     -> 5 V
- (schwarz) -> GND
D (weiß)    -> GPIO 2 oder GPIO 4
```

GPIO 2 ist in WLED der Standard-Datenpin; GPIO 4 funktioniert ebenfalls und lässt sich in WLED einstellen.

### Stromversorgung

Die 84 LEDs **nicht** über das ESP32-Board versorgen – der Strom kann für Board, Spannungsregler oder USB-Buchse zu hoch sein. Das 5-V-Netzteil direkt an die Panels anschließen und den ESP32 parallel dazu:

```text
Netzteil 5 V +   -> Panels +
                 -> ESP32 5 V

Netzteil 5 V -   -> Panels -
                 -> ESP32 GND

ESP32 GPIO 2/4   -> Panels D
```

- ESP32 und Panels brauchen eine gemeinsame Masse (GND).
- Wer das originale zweiadrige USB-Stromkabel weiterverwendet: vorher die Polarität mit dem Multimeter prüfen. Bei @Nisbo war Rot 5 V und **Weiß GND**.
- Den ESP32 nicht gleichzeitig an USB und an das externe 5-V-Netzteil hängen, außer das Board ist gegen Rückspeisung geschützt.

---

## WLED-Einstellungen

**Config → LED Preferences:**

| Einstellung | Wert |
|-------------|------|
| LED type | WS281x |
| LED count | 84 |
| GPIO | 2 oder 4 |
| Color order | GRB |

## Segmente: eins pro Hexagon

Der folgende Befehl legt 13 Segmente an: Segment 0 umfasst alle 84 LEDs, Segment 1–12 sind die einzelnen Panels (je 7 LEDs). `192.168.179.160` durch die IP-Adresse des eigenen WLED-Geräts ersetzen. Die Panelnamen (`Panel_<Spalte>_<Reihe>`) beschreiben @Nisbos Anordnung – an die eigene anpassen.

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

### Aufteilung als Preset speichern

```bash
curl -X POST "http://192.168.179.160/json/state" \
  -H "Content-Type: application/json" \
  -d '{"psave": 1, "n": "Grundaufteilung", "sb": true}'
```

Damit ist die Segment-Aufteilung als Preset `1` „Grundaufteilung“ gespeichert. In WLED auswählen, um sie wiederherzustellen, oder automatisch beim Start laden:

```text
Config -> LED Preferences -> Apply preset at boot -> 1
```
