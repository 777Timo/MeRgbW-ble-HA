import colorsys

from .effect_names import LANGUAGES, LEGACY_SCENE_ALIASES, MUSIC_NAMES, NO_EFFECT, SCENE_NAMES

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


# Effect names per language, extracted from the MeRGBW app (see scripts/generate_effect_names.py)
EFFECT_SCENE = "scene"
EFFECT_MUSIC = "music"


def resolve_language(language: str | None) -> str:
    """Map the Home Assistant language (e.g. "en-GB", "zh-Hant") to a supported one, fallback English."""
    if language in LANGUAGES:
        return language
    base = (language or "").split("-")[0]
    if base == "zh":
        return "zh-Hans"
    return base if base in LANGUAGES else "en"


def effect_list(language: str) -> list[str]:
    scenes = SCENE_NAMES[language]
    music = MUSIC_NAMES[language]
    return [scenes[i] for i in sorted(scenes)] + [music[i] for i in sorted(music)]


def effect_name(language: str, kind: str, index: int) -> str:
    return (SCENE_NAMES if kind == EFFECT_SCENE else MUSIC_NAMES)[language][index]


# Every name in every language -> (kind, index). Automations keep working no matter
# which language Home Assistant is set to.
EFFECT_LOOKUP: dict[str, tuple[str, int]] = {}
for _lang in LANGUAGES:
    EFFECT_LOOKUP.update({n: (EFFECT_SCENE, i) for i, n in SCENE_NAMES[_lang].items()})
    EFFECT_LOOKUP.update({n: (EFFECT_MUSIC, i) for i, n in MUSIC_NAMES[_lang].items()})
for _index, _aliases in LEGACY_SCENE_ALIASES.items():
    EFFECT_LOOKUP.update({n: (EFFECT_SCENE, _index) for n in _aliases})


def cmd_effect(kind: str, index: int) -> bytes:
    return cmd_scene(index) if kind == EFFECT_SCENE else cmd_music_mode(index)


def cmd_scene(index: int) -> bytes:
    """Select a built-in scene by 1-based index (1–113+)."""
    payload = bytes([0x55, 0x06, 0xFF, 0x07, (index >> 8) & 0xFF, index & 0xFF])
    return payload + bytes([_checksum(payload)])


def cmd_scene_speed(speed_pct: int) -> bytes:
    """Set scene animation speed (0–100%). Device uses delay internally: 0=fastest, 100=slowest."""
    speed = max(0, min(100, 100 - speed_pct))
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
