# MeRgbW BLE — Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![HA Version](https://img.shields.io/badge/Home%20Assistant-2024.1%2B-blue)](https://www.home-assistant.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

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
- **115 built-in scenes / animations**
- **6 music-reactive modes** (microphone-based)
- Animation speed control (0–100 %)
- Microphone sensitivity control (0–100 %)
- Automatic BLE discovery via Home Assistant Bluetooth integration
- Manual setup by MAC address as fallback
- State polling on startup (power state + brightness)
- Raw BLE debug command input for development
- 100 % local — no internet connection required

---

### Entities

| Entity | Type | Description |
|--------|------|-------------|
| `light.<name>` | Light | On/Off, RGB color, brightness, effect selection (115 scenes) |
| `select.<name>_effect` | Select | Choose scene or music mode from a dropdown |
| `number.<name>_animation_speed` | Number | Animation speed 0–100 % |
| `number.<name>_music_sensitivity` | Number | Microphone sensitivity 0–100 % |
| `text.<name>_ble_debug` | Text | Send raw hex BLE commands (for development) |

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
5. Alternatively, go to **Settings → Devices & Services → + Add Integration → Hexagon BLE Lights** and enter the MAC address manually.

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
- **115 eingebaute Szenen / Animationen**
- **6 musikreaktive Modi** (Mikrofonbasiert)
- Animationsgeschwindigkeit (0–100 %)
- Mikrofonempfindlichkeit (0–100 %)
- Automatische BLE-Erkennung über Home Assistant Bluetooth-Integration
- Manuelles Setup per MAC-Adresse als Fallback
- Statusabfrage beim Start (Ein/Aus-Zustand + Helligkeit)
- Rohe BLE-Debug-Befehle für die Entwicklung
- 100 % lokal — keine Internetverbindung erforderlich

---

### Entities (HA-Entitäten)

| Entity | Typ | Beschreibung |
|--------|-----|--------------|
| `light.<name>` | Licht | Ein/Aus, RGB-Farbe, Helligkeit, Effektauswahl (115 Szenen) |
| `select.<name>_effect` | Auswahl | Szene oder Musikmodus per Dropdown |
| `number.<name>_animation_speed` | Zahl | Animationsgeschwindigkeit 0–100 % |
| `number.<name>_music_sensitivity` | Zahl | Mikrofonempfindlichkeit 0–100 % |
| `text.<name>_ble_debug` | Text | Rohe BLE-Hex-Befehle senden (für Entwicklung) |

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
5. Alternativ: **Einstellungen → Geräte & Dienste → + Integration hinzufügen → Hexagon BLE Lights** und MAC-Adresse manuell eingeben.

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

---

### Lizenz

MIT-Lizenz — siehe [LICENSE](LICENSE)
