import colorsys

DOMAIN = "hexagon_ble"

WRITE_CHAR_UUID = "0000fff3-0000-1000-8000-00805f9b34fb"
NOTIFY_CHAR_UUID = "0000fff4-0000-1000-8000-00805f9b34fb"

# Protocol: 0x55-header, checksum = (0xFF - sum(preceding_bytes)) & 0xFF
CMD_ON  = bytes.fromhex("5501ff0601a3")
CMD_OFF = bytes.fromhex("5501ff0600a4")


def _checksum(data: bytes) -> int:
    return (0xFF - (sum(data) & 0xFF)) & 0xFF


def cmd_color(r: int, g: int, b: int) -> bytes:
    """Convert RGB to HSV and encode as 9-byte color command."""
    h, s, _v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    hue = round(h * 360)    # 0–360 degrees, uint16 big-endian
    sat = round(s * 1000)   # 0–1000, uint16 big-endian
    payload = bytes([
        0x55, 0x03, 0xFF, 0x09,
        (hue >> 8) & 0xFF, hue & 0xFF,
        (sat >> 8) & 0xFF, sat & 0xFF,
    ])
    return payload + bytes([_checksum(payload)])


def cmd_brightness(brightness_255: int) -> bytes:
    """Encode HA brightness (0–255) as 7-byte brightness command (device scale 0–1000)."""
    val = round(brightness_255 / 255 * 1000)
    payload = bytes([0x55, 0x05, 0xFF, 0x07, (val >> 8) & 0xFF, val & 0xFF])
    return payload + bytes([_checksum(payload)])


# Scene names extracted from MeRGBW app (de.lproj/Localizable.strings)
# Key = BLE scene index, value = display name
SCENE_NAMES: dict[int, str] = {
    1: "Zyklus", 2: "Phantasiefarbe", 3: "Siebenfarbige Energie",
    4: "Siebenfarbiger Sprung", 5: "Rot-Grün-Blau-Sprung", 6: "Gelb-Cyan-Lila-Sprung",
    7: "Siebenfarbiger Blinker", 8: "Rot-Grün-Blau-Blinker", 9: "Gelb-Cyan-Lila-Blinker",
    10: "Siebenfarbiger Gradient", 11: "Rot-Gelb-Wechselgradient", 12: "Rot-Lila-Wechselgradient",
    13: "Grün-Cyan-Wechselgradient", 14: "Grün-Gelb-Wechselgradient", 15: "Blau-Lila-Wechselgradient",
    16: "Rot-Akkumulation", 17: "Grün-Akkumulation", 18: "Blau-Akkumulation",
    19: "Gelb-Akkumulation", 20: "Cyan-Akkumulation", 21: "Lila-Akkumulation",
    22: "Weiß-Akkumulation", 23: "Siebenfarbige Verfolgung", 24: "Rot-Grün-Blau-Verfolgung",
    25: "Gelb-Cyan-Lila-Verfolgung", 26: "Siebenfarbige Drift", 27: "Rot-Grün-Blau-Drift",
    28: "Gelb-Cyan-Lila-Drift", 29: "Siebenfarbige Streichen", 30: "Rot-Grün-Blau-Streichen",
    31: "Gelb-Cyan-Streichen", 32: "Siebenfarbige Melodie-Schluss",
    33: "Rot-Grün-Blau-Melodie-Schluss", 34: "Gelb-Cyan-Lila-Melodie-Schluss",
    35: "Siebenfarbige Öffnung", 36: "Rot-Grün-Blau-Öffnung", 37: "Gelb-Cyan-Lila-Öffnung",
    38: "Rot-Öffnung", 39: "Grün-Öffnung", 40: "Blau-Öffnung",
    41: "Gelb-Öffnung", 42: "Cyan-Öffnung", 43: "Lila-Öffnung", 44: "Weiß-Öffnung",
    45: "Siebenfarbiger Helligkeitsübergang", 46: "RGB-Helligkeitsübergang",
    47: "Lila-Cyan-Gelb-Helligkeitsübergang",
    48: "Dunkelübergang Rot", 49: "Dunkelübergang Grün", 50: "Dunkelübergang Blau",
    51: "Dunkelübergang Cyan", 52: "Dunkelübergang Gelb", 53: "Dunkelübergang Lila",
    54: "Dunkelübergang Weiß",
    55: "Siebenfarbiges Wasser", 56: "RGB-Fließendes Wasser", 57: "Cyan-Gelb-Lila-Wasser",
    58: "Rot-Grün-Wasser", 59: "Grün-Blau-Wasser", 60: "Gelb-Blau-Wasser",
    61: "Gelb-Cyan-Wasser", 62: "Cyan-Lila-Wasser", 63: "Schwarz-Weiß-Wasser",
    64: "Weiß-Rot-Weiß-Fluss", 65: "Weiß-Grün-Weiß-Fluss", 66: "Weiß-Blau-Weiß-Fluss",
    67: "Weiß-Gelb-Weiß-Fluss", 68: "Weiß-Cyan-Weiß-Fluss", 69: "Weiß-Lila-Weiß-Fluss",
    70: "Rot-Weiß-Rot-Fluss", 71: "Grün-Weiß-Grün-Fluss", 72: "Blau-Weiß-Blau-Fluss",
    73: "Gelb-Weiß-Gelb-Fluss", 74: "Cyan-Weiß-Cyan-Fluss", 75: "Lila-Weiß-Lila-Fluss",
    # 76-83 not defined in app
    84: "Rot-Lauf", 85: "Grün-Lauf", 86: "Blau-Lauf", 87: "Gelb-Lauf",
    88: "Cyan-Lauf", 89: "Lila-Lauf", 90: "Weiß-Lauf",
    91: "Siebenfarbiger Lauf", 92: "RGB-Lauf", 93: "Lila-Cyan-Gelb-Lauf",
    94: "Blau-Lila-Cyan-Gelb-Lauf", 95: "Blau-Grün-Cyan-Gelb-Lauf",
    96: "Rot-Punkt/Weiß", 97: "Grün-Punkt/Rot", 98: "Blau-Punkt/Grün",
    99: "Gelb-Punkt/Blau", 100: "Cyan-Punkt/Gelb", 101: "Lila-Punkt/Cyan",
    102: "Weiß-Punkt/Lila", 103: "Weiß-Punkt/Rot",
    104: "Bunt-Punkt/Rot", 105: "Bunt-Punkt/Grün", 106: "Bunt-Punkt/Blau",
    107: "Bunt-Punkt/Gelb", 108: "Bunt-Punkt/Cyan", 109: "Bunt-Punkt/Lila",
    110: "Bunt-Punkt/Weiß", 111: "Grün-Punkt/Blau", 112: "Grün-Punkt/Rot2",
    113: "Rot-Punkt/Blau", 114: "Cyan-Punkt/Gelb2", 115: "Lila-Punkt/Gelb",
    116: "Weiß-Punkt/Gelb", 117: "Gelb-Punkt/Weiß",
}
# Music modes (type=0x07, index 1-6)
MUSIC_NAMES: dict[int, str] = {
    1: "Musik: Intervall-Wechsel",
    2: "Musik: Bewegen",
    3: "Musik: Fließen",
    4: "Musik: Atmen",
    5: "Musik: Spektrum1",
    6: "Musik: Spektrum2",
}
MUSIC_INDEX: dict[str, int] = {v: k for k, v in MUSIC_NAMES.items()}

SCENE_INDEX: dict[str, int] = {v: k for k, v in SCENE_NAMES.items()}
EFFECT_LIST: list[str] = (
    [SCENE_NAMES[i] for i in sorted(SCENE_NAMES.keys())]
    + [MUSIC_NAMES[i] for i in sorted(MUSIC_NAMES.keys())]
)


def cmd_scene(index: int) -> bytes:
    """Select a built-in scene by 1-based index (1–113+)."""
    payload = bytes([0x55, 0x06, 0xFF, 0x07, (index >> 8) & 0xFF, index & 0xFF])
    return payload + bytes([_checksum(payload)])


def cmd_scene_speed(speed_pct: int) -> bytes:
    """Set scene animation speed (0–100%). Type 0x0F, 6-byte format (verified)."""
    speed = max(0, min(100, speed_pct))
    payload = bytes([0x55, 0x0F, 0xFF, 0x06, speed])
    return payload + bytes([_checksum(payload)])


def cmd_music_mode(index: int) -> bytes:
    """Select music-reactive mode (1–6)."""
    payload = bytes([0x55, 0x07, 0xFF, 0x06, index])
    return payload + bytes([_checksum(payload)])


def cmd_music_sensitivity(sensitivity_pct: int) -> bytes:
    """Set microphone sensitivity (0–100%)."""
    val = max(0, min(100, sensitivity_pct))
    payload = bytes([0x55, 0x08, 0xFF, 0x06, val])
    return payload + bytes([_checksum(payload)])
