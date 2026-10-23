# MeRgbW BLE — Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![HA Version](https://img.shields.io/badge/Home%20Assistant-2024.1%2B-blue)](https://www.home-assistant.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Vibe Coded](https://img.shields.io/badge/vibe%20coded-with%20Claude-blueviolet)](https://claude.ai)

> **Unofficial integration — not affiliated with or endorsed by MeRGBW / Shenzhen Minjie Technology.**

> **[English](#english) | [Deutsch](#deutsch)**

---

<a name="english"></a>

## 🇬🇧 English

### Overview

Custom Home Assistant integration to control **MeRgbW Hexagon LED panels** via Bluetooth Low Energy (BLE).  
Fully reverse-engineered from the official MeRGBW iOS app — no cloud, no account required.

Supports **automatic Bluetooth discovery** and provides full control over color, brightness, animations, and music-reactive modes directly from Home Assistant.

---

### Features

- Full RGB color control (internally converted to HSV — matches the device's native color space)
- Brightness control (0–100 %)
- **109 built-in scenes / animations**
- **6 music-reactive modes** (microphone-based)
- Animation speed control (0–100 %)
- Microphone sensitivity control (0–100 %)
- Automatic BLE discovery via Home Assistant Bluetooth integration
- Manual setup by MAC address as fallback
- **Localized** in English, German, Spanish, French, Italian and Chinese (Simplified) — follows the Home Assistant language
- 100 % local — no internet connection required

---

### Entities

| Entity | Type | Description |
|--------|------|-------------|
| `light.<name>` | Light | On/Off, RGB color, brightness, effect selection (109 scenes + 6 music modes) |
| `select.<name>_effect` | Select | Choose scene or music mode from a dropdown |
| `number.<name>_animation_speed` | Number | Animation speed 0–100 % |
| `number.<name>_music_sensitivity` | Number | Microphone sensitivity 0–100 % |

Home Assistant creates the entity IDs when the device is added, so their suffix can differ with your language (e.g. `number.<name>_animationsgeschwindigkeit` on a German system).

---

### Requirements

- Home Assistant **2024.1** or newer
- Bluetooth adapter accessible to Home Assistant:
  - USB Bluetooth dongle connected to your HA host, **or**
  - [ESPHome Bluetooth Proxy](https://esphome.io/components/bluetooth_proxy.html) in range of the light

---

### Installation

#### Via HACS (recommended)

1. Open HACS in your Home Assistant instance.
2. Go to **Integrations** → click the **⋮ menu** (top right) → **Custom repositories**.
3. Add:
   - **URL:** `https://github.com/777Timo/MeRgbW-ble-HA`
   - **Category:** Integration
4. Search for **MeRgbW BLE** and install it.
5. Restart Home Assistant.

#### Manual Installation

1. Download or clone this repository.
2. Copy the `custom_components/hexagon_ble/` folder into your Home Assistant configuration directory:
   ```
   config/custom_components/hexagon_ble/
   ```
3. Restart Home Assistant.

---

### Configuration

1. Make sure your Bluetooth adapter is working in Home Assistant (check **Settings → System → Hardware**).
2. Power on your MeRgbW light and bring it within Bluetooth range.
3. Home Assistant will **automatically discover** the device and show a notification.
4. Click **Configure** and confirm the device.
5. Alternatively, go to **Settings → Devices & Services → + Add Integration → MeRgbW BLE** and enter the MAC address manually.

> **Close the MeRGBW app first.** The light accepts only one Bluetooth connection at a time. While it is connected to the app on your phone, Home Assistant can neither discover it nor connect to it — this also applies to manual setup by MAC address. Close the app or turn off Bluetooth on the phone.

---

### Languages

Entity names, the setup dialog and all effect names follow the Home Assistant language (**Settings → System → General**). Supported: English, German, Spanish, French, Italian, Chinese (Simplified); any other language falls back to English. The effect names are taken from the official MeRGBW app.

In automations and scripts you can use the effect name in **any** of these languages — `Rot-Gelb-Wechselgradient` and `Red-yellow alternating gradient` both select scene 11. Existing automations therefore keep working after switching the language.

---

### Limitations

- **No individual color per panel.** The integration sets one color, scene or music mode for the whole light. A per-panel command of the BLE controller is not known yet. If you need per-panel control, the original controller can be replaced with an ESP32 running WLED — see [this guide by @Nisbo](https://github.com/777Timo/MeRgbW-ble-HA/issues/1#issuecomment-5061774110).
- Color, effect, speed and sensitivity are not reported back by the device; Home Assistant shows the last values it sent.

---

### BLE Protocol (Technical Reference)

> This section documents the reverse-engineered BLE protocol for development purposes.

**BLE Characteristics:**

| Role | UUID |
|------|------|
| Write (WWR) | `0000fff3-0000-1000-8000-00805f9b34fb` |
| Notify | `0000fff4-0000-1000-8000-00805f9b34fb` |
| Discovery service | `00003519-0000-1000-8000-00805f9b34fb` |

**Frame format:** `55 [type] FF [len] [data...] [checksum]`  
**Checksum:** `(0xFF - sum(all_preceding_bytes)) & 0xFF`

| Type | Function | Data format |
|------|----------|-------------|
| `01` | Power | `01` = ON, `00` = OFF |
| `03` | Color (HSV) | Hue uint16 BE (0–360°), Sat uint16 BE (0–1000) |
| `05` | Brightness | uint16 BE (0–1000) |
| `06` | Scene | Index uint16 BE (1–117) |
| `07` | Music mode | Index `01`–`06` |
| `08` | Music sensitivity | `00`–`64` (0–100 %) |
| `0F` | Scene speed | `00`–`64` (device: 0 = fastest, inverted in integration) |
| `00` | State query | No data — device responds with power + brightness |

**State query response:** `56 00 FF [payload] [checksum]`  
- `payload[1]`: `01` = ON, `00` = OFF  
- `payload[2..3]`: Brightness uint16 BE (0–1000)  
- Color and scene are **not** reported by the device — tracked locally.

---

### Contributing

Pull requests and issues are welcome. Please open an issue before submitting large changes.

The effect names are generated from the MeRGBW app: `python3 scripts/generate_effect_names.py <path to LEDProject.app>` writes `custom_components/hexagon_ble/effect_names.py`.

---

### Changelog

- **1.1.0** — Translations (en, de, es, fr, it, zh-Hans) for entities, setup dialog and effect names; effect names in automations work in every language; hint about the MeRGBW app blocking the connection; log messages in English. Thanks to [@AshBringer47](https://github.com/AshBringer47) for the first English translation in their fork.
- **1.0.0** — Initial release.

---

### Vibe Coded

This integration was fully vibe coded with [Claude](https://claude.ai) — BLE protocol reverse-engineered, integration written, and bugs squashed entirely through AI-assisted development.

---

### License

MIT License — see [LICENSE](LICENSE)

---

<a name="deutsch"></a>

## 🇩🇪 Deutsch

### Übersicht

Custom Home Assistant Integration zur Steuerung von **MeRgbW Hexagon LED-Panels** über Bluetooth Low Energy (BLE).  
Vollständig per Reverse Engineering aus der offiziellen MeRGBW iOS-App entwickelt — kein Cloud-Account erforderlich.

Unterstützt **automatische Bluetooth-Erkennung** und bietet vollständige Kontrolle über Farbe, Helligkeit, Animationen und musik-reaktive Modi direkt aus Home Assistant heraus.

---

### Funktionen

- Vollständige RGB-Farbsteuerung (intern in HSV umgerechnet — entspricht dem nativen Farbraum des Geräts)
- Helligkeitssteuerung (0–100 %)
- **109 eingebaute Szenen / Animationen**
- **6 musikreaktive Modi** (Mikrofonbasiert)
- Animationsgeschwindigkeit (0–100 %)
- Mikrofonempfindlichkeit (0–100 %)
- Automatische BLE-Erkennung über Home Assistant Bluetooth-Integration
- Manuelles Setup per MAC-Adresse als Fallback
- **Mehrsprachig**: Deutsch, Englisch, Spanisch, Französisch, Italienisch und Chinesisch (vereinfacht) — richtet sich nach der Sprache von Home Assistant
- 100 % lokal — keine Internetverbindung erforderlich

---

### Entities (HA-Entitäten)

| Entity | Typ | Beschreibung |
|--------|-----|--------------|
| `light.<name>` | Licht | Ein/Aus, RGB-Farbe, Helligkeit, Effektauswahl (109 Szenen + 6 Musikmodi) |
| `select.<name>_effect` | Auswahl | Szene oder Musikmodus per Dropdown |
| `number.<name>_animation_speed` | Zahl | Animationsgeschwindigkeit 0–100 % |
| `number.<name>_music_sensitivity` | Zahl | Mikrofonempfindlichkeit 0–100 % |

Home Assistant legt die Entity-IDs beim Hinzufügen des Geräts an; die Endung kann daher je nach Sprache abweichen (z. B. `number.<name>_animationsgeschwindigkeit` auf einem deutschen System).

---

### Voraussetzungen

- Home Assistant **2024.1** oder neuer
- Bluetooth-Adapter, der von Home Assistant erreichbar ist:
  - USB-Bluetooth-Dongle am HA-Host, **oder**
  - [ESPHome Bluetooth Proxy](https://esphome.io/components/bluetooth_proxy.html) in Reichweite der Leuchte

---

### Installation

#### Über HACS (empfohlen)

1. HACS in Home Assistant öffnen.
2. **Integrationen** → **⋮-Menü** (oben rechts) → **Benutzerdefinierte Repositories**.
3. Eintragen:
   - **URL:** `https://github.com/777Timo/MeRgbW-ble-HA`
   - **Kategorie:** Integration
4. Nach **MeRgbW BLE** suchen und installieren.
5. Home Assistant neu starten.

#### Manuelle Installation

1. Repository herunterladen oder klonen.
2. Den Ordner `custom_components/hexagon_ble/` in das Home Assistant Konfigurationsverzeichnis kopieren:
   ```
   config/custom_components/hexagon_ble/
   ```
3. Home Assistant neu starten.

---

### Konfiguration

1. Sicherstellen, dass der Bluetooth-Adapter in Home Assistant funktioniert (**Einstellungen → System → Hardware**).
2. MeRgbW-Leuchte einschalten und in Bluetooth-Reichweite bringen.
3. Home Assistant erkennt das Gerät **automatisch** und zeigt eine Benachrichtigung an.
4. Auf **Konfigurieren** klicken und das Gerät bestätigen.
5. Alternativ: **Einstellungen → Geräte & Dienste → + Integration hinzufügen → MeRgbW BLE** und MAC-Adresse manuell eingeben.

> **Vorher die MeRGBW-App schließen.** Die Leuchte nimmt nur eine Bluetooth-Verbindung gleichzeitig an. Solange sie mit der App auf dem Handy verbunden ist, kann Home Assistant sie weder finden noch sich verbinden — auch nicht beim manuellen Hinzufügen per MAC-Adresse. App schließen oder Bluetooth am Handy ausschalten.

---

### Sprachen

Entitätsnamen, Einrichtungsdialog und alle Effektnamen richten sich nach der Sprache von Home Assistant (**Einstellungen → System → Allgemein**). Unterstützt: Deutsch, Englisch, Spanisch, Französisch, Italienisch, Chinesisch (vereinfacht); andere Sprachen fallen auf Englisch zurück. Die Effektnamen stammen aus der offiziellen MeRGBW-App.

In Automationen und Skripten funktioniert der Effektname in **jeder** dieser Sprachen — `Rot-Gelb-Wechselgradient` und `Red-yellow alternating gradient` wählen beide Szene 11. Bestehende Automationen laufen deshalb auch nach einem Sprachwechsel weiter.

---

### Einschränkungen

- **Keine eigene Farbe pro Panel.** Die Integration setzt eine Farbe, Szene oder einen Musikmodus für die ganze Leuchte. Ein Befehl für einzelne Panels ist beim BLE-Controller bisher nicht bekannt. Wer jedes Panel einzeln steuern möchte, kann den Original-Controller durch einen ESP32 mit WLED ersetzen — siehe [diese Anleitung von @Nisbo](https://github.com/777Timo/MeRgbW-ble-HA/issues/1#issuecomment-5061774110).
- Farbe, Effekt, Geschwindigkeit und Empfindlichkeit meldet das Gerät nicht zurück; Home Assistant zeigt die zuletzt gesendeten Werte.

---

### BLE-Protokoll (Technische Referenz)

> Dieser Abschnitt dokumentiert das per Reverse Engineering ermittelte BLE-Protokoll für Entwicklungszwecke.

**BLE-Charakteristiken:**

| Rolle | UUID |
|-------|------|
| Schreiben (WWR) | `0000fff3-0000-1000-8000-00805f9b34fb` |
| Notify | `0000fff4-0000-1000-8000-00805f9b34fb` |
| Discovery-Service | `00003519-0000-1000-8000-00805f9b34fb` |

**Frame-Format:** `55 [type] FF [len] [data...] [checksum]`  
**Prüfsumme:** `(0xFF - sum(alle_vorherigen_Bytes)) & 0xFF`

| Typ | Funktion | Datenformat |
|-----|----------|-------------|
| `01` | Ein/Aus | `01` = AN, `00` = AUS |
| `03` | Farbe (HSV) | Hue uint16 BE (0–360°), Sat uint16 BE (0–1000) |
| `05` | Helligkeit | uint16 BE (0–1000) |
| `06` | Szene | Index uint16 BE (1–117) |
| `07` | Musikmodus | Index `01`–`06` |
| `08` | Musikempfindlichkeit | `00`–`64` (0–100 %) |
| `0F` | Szenen-Geschwindigkeit | `00`–`64` (Gerät: 0 = schnellste, invertiert in Integration) |
| `00` | Statusabfrage | Keine Daten — Gerät antwortet mit Zustand + Helligkeit |

**Statusabfrage-Antwort:** `56 00 FF [payload] [checksum]`  
- `payload[1]`: `01` = AN, `00` = AUS  
- `payload[2..3]`: Helligkeit uint16 BE (0–1000)  
- Farbe und Szene werden vom Gerät **nicht** zurückgemeldet — werden lokal getrackt.

---

### Mitarbeit

Pull Requests und Issues sind willkommen. Bitte ein Issue erstellen, bevor umfangreiche Änderungen eingereicht werden.

Die Effektnamen werden aus der MeRGBW-App erzeugt: `python3 scripts/generate_effect_names.py <Pfad zu LEDProject.app>` schreibt `custom_components/hexagon_ble/effect_names.py`.

---

### Änderungen

- **1.1.0** — Übersetzungen (de, en, es, fr, it, zh-Hans) für Entitäten, Einrichtungsdialog und Effektnamen; Effektnamen funktionieren in Automationen in jeder Sprache; Hinweis, dass die MeRGBW-App die Verbindung blockiert; Log-Meldungen auf Englisch. Danke an [@AshBringer47](https://github.com/AshBringer47) für die erste englische Übersetzung in deren Fork.
- **1.0.0** — Erste Version.

---

### Vibe Coded

Diese Integration wurde vollständig mit [Claude](https://claude.ai) vibe gecodet — BLE-Protokoll per Reverse Engineering ermittelt, Integration geschrieben und Bugs behoben, alles durch KI-gestützte Entwicklung.

---

### Lizenz

MIT-Lizenz — siehe [LICENSE](LICENSE)
