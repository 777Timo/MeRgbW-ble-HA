#!/usr/bin/env python3
"""Generate custom_components/hexagon_ble/effect_names.py from the MeRGBW app.

The scene and music mode names come from the app's Localizable.strings files
(keys mode_<index>, effect_01..04, title_spectrum1/2, title_music). The app
bundle is not part of this repository; point the script at it:

    python3 scripts/generate_effect_names.py /path/to/LEDProject.app

On macOS with the iOS app installed: /Applications/MeRGBW.app/Wrapper/LEDProject.app

German keeps the short names this integration has always used, so existing
automations keep working. The app's es/fr/it texts contain machine-translation
leftovers ("with", "on", "a fonds"), which are cleaned up below.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

LANGUAGES = ["de", "en", "es", "fr", "it", "zh-Hans"]
SCENE_INDICES = list(range(1, 76)) + list(range(84, 118))  # 76-83 not defined in app
MUSIC_KEYS = ["effect_01", "effect_02", "effect_03", "effect_04", "title_spectrum1", "title_spectrum2"]

# Short German names (unchanged since v1.0.0, except 115, see SCENE_FIXES).
DE_SCENES: dict[int, str] = {
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
    113: "Rot-Punkt/Blau", 114: "Cyan-Punkt/Gelb2", 115: "Gelb-Punkt/Lila",
    116: "Weiß-Punkt/Gelb", 117: "Gelb-Punkt/Weiß",
}

# Scene 115 is "purple background, yellow dot" in the original Chinese text
# (紫底黄点跑动) and in English; de/es/fr/it swapped the colours.
SCENE_FIXES: dict[str, dict[int, str]] = {
    "es": {115: "Correr con un punto amarillo en el fondo morado"},
    "fr": {115: "Marche avec un point jaune sur un fond violet"},
    "it": {115: "Corsa con un punto giallo sullo sfondo violetto"},
}

# Names that were valid in earlier versions; still accepted as input.
LEGACY_ALIASES: dict[int, list[str]] = {115: ["Lila-Punkt/Gelb"]}

NO_EFFECT: dict[str, str] = {
    "de": "Kein Effekt (Farbe)",
    "en": "No effect (color)",
    "es": "Sin efecto (color)",
    "fr": "Aucun effet (couleur)",
    "it": "Nessun effetto (colore)",
    "zh-Hans": "无效果（颜色）",
}


def clean(lang: str, text: str) -> str:
    text = " ".join(text.split())
    if lang == "es":
        text = text.replace("Correr with ", "Correr con ").replace(" in el fondo", " en el fondo")
    elif lang == "fr":
        text = text.replace("avec a point", "avec un point").replace("sur a fonds", "sur un fond")
    elif lang == "it":
        text = re.sub(r"^Corsa with a punto (\S+) on (\S+)$", r"Corsa con un punto \1 sullo sfondo \2", text)
        text = text.replace("Corsa with a punto", "Corsa con un punto").replace("Corsa con a punto", "Corsa con un punto")
        text = text.replace("v-ioletto", "violetto").replace("oscurité", "oscurità").replace("( ", "(")
    return text[:1].upper() + text[1:]


def dedupe(names: dict[int, str]) -> dict[int, str]:
    """HA needs unique effect names; the app reuses two texts (97/112, 100/114)."""
    seen: set[str] = set()
    out: dict[int, str] = {}
    for idx, name in names.items():
        if name in seen:
            name = f"{name} 2"
        seen.add(name)
        out[idx] = name
    return out


def load_strings(app: Path, lang: str) -> dict[str, str]:
    raw = subprocess.run(
        ["plutil", "-convert", "json", "-o", "-", str(app / f"{lang}.lproj" / "Localizable.strings")],
        check=True, capture_output=True,
    ).stdout
    return json.loads(raw)


def main() -> None:
    app = Path(sys.argv[1])
    scenes: dict[str, dict[int, str]] = {}
    music: dict[str, dict[int, str]] = {}
    for lang in LANGUAGES:
        strings = load_strings(app, lang)
        if lang == "de":
            names = dict(DE_SCENES)
        else:
            names = {i: clean(lang, strings[f"mode_{i}"]) for i in SCENE_INDICES}
            names.update(SCENE_FIXES.get(lang, {}))
        scenes[lang] = dedupe(names)
        prefix = strings["title_music"].strip()
        music[lang] = {
            i + 1: f"{prefix}: {clean(lang, strings[key])}" for i, key in enumerate(MUSIC_KEYS)
        }

    out = Path(__file__).resolve().parent.parent / "custom_components" / "hexagon_ble" / "effect_names.py"
    lines = [
        '"""Localized effect names. Generated by scripts/generate_effect_names.py – do not edit."""',
        "",
        f"LANGUAGES: tuple[str, ...] = {tuple(LANGUAGES)!r}",
        "",
        "# language -> BLE scene index -> display name",
        "SCENE_NAMES: dict[str, dict[int, str]] = {",
    ]
    for lang in LANGUAGES:
        lines.append(f"    {lang!r}: {{")
        lines += [f"        {i}: {n!r}," for i, n in scenes[lang].items()]
        lines.append("    },")
    lines += ["}", "", "# language -> music mode index -> display name", "MUSIC_NAMES: dict[str, dict[int, str]] = {"]
    for lang in LANGUAGES:
        lines.append(f"    {lang!r}: {{")
        lines += [f"        {i}: {n!r}," for i, n in music[lang].items()]
        lines.append("    },")
    lines += ["}", "", f"NO_EFFECT: dict[str, str] = {NO_EFFECT!r}", ""]
    lines += [f"LEGACY_SCENE_ALIASES: dict[int, list[str]] = {LEGACY_ALIASES!r}", ""]
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
