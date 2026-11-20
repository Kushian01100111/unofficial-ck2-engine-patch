#!/usr/bin/env python3
"""Build a separate experimental CK2 3.3.5.1 installation."""
import argparse
import hashlib
import os
from pathlib import Path
import re
import shutil
import subprocess

import load_save

EXE_HASH = "a0cc8e92287ac900b0552f5cca20df5acedf4773244923a77b15bcdbe143b13d"
SCRIPT_HASH = "6c80146d5d9808325cf0e1b5453370de5bd994692488db42014531d0b3997632"
IRONMAN_TOOLTIP = Path("localisation/v2_00.csv")
IRONMAN_TOOLTIP_HASH = "735901e49bba4b7d3c5d01831ed4e43d7a0546f5c78a073582a00ca1a9a69a66"
CONTINUE_DIALOG = Path("localisation/ReapersDue.csv")
CONTINUE_DIALOG_HASH = "92a674ba84096084f0bd591617e66131537b8e488808ea5991f5c82cc26c00e6"
ACHIEVEMENT_TEXT = {
    CONTINUE_DIALOG: (CONTINUE_DIALOG_HASH, {
        "RULES_ACHIEVEMENT_REQUIRE_IRONMAN": ("", "", "", ""),
        "RULES_ACHIEVEMENT_REQUIRE_NOMOD": (
            "Game data checksum check", "Contrôle de la somme de contrôle du jeu",
            "Prüfsummenprüfung der Spieldaten", "Comprobación de la suma de los datos del juego",
        ),
    }),
    Path("localisation/v2_40c.csv"): (
        "8b9c1645d330313e7279271906af8036739737008d59cce062508e0d7b7d67a8", {
            "IRONMAN_MODE_CHECKSUM_DESC": (
                "The game data files have been modified.", "Les fichiers du jeu ont été modifiés.",
                "Die Spieldateien wurden verändert.", "Se han modificado los archivos del juego.",
            ),
        },
    ),
    Path("localisation/v2_81.csv"): (
        "a78566eb57a938af28f7c987df0e117414edabb260dc50fb046adad014451d00", {
            "RULES_ACHIEVEMENT_REQUIRE_NO_RULER_DESIGNER": (
                "Ruler Designer eligibility check", "Contrôle du créateur de personnage",
                "Prüfung des Herrscher-Baukastens", "Comprobación del Diseñador de gobernante",
            ),
            "IRONMAN_MODE_RULER_DESIGNER_DESC": (
                "The Ruler Designer is active.", "Le créateur de personnage est actif.",
                "Der Herrscher-Baukasten ist aktiv.", "El Diseñador de gobernante está activo.",
            ),
        },
    ),
    Path("localisation/RedKing.csv"): (
        "dd9f84cc7889fb391bcf4dbc6937819d3db6c21e293859388bfef515cbb86e6b", {
            "BRONZEMAN_MODE_DESC": (
                "Bronzeman mode allows multiple saves per campaign.",
                "Le mode Bronzeman permet plusieurs sauvegardes par campagne.",
                "Im Bronzeman-Modus sind mehrere Spielstände pro Kampagne möglich.",
                "El modo Bronzeman permite varias partidas guardadas por campaña.",
            ),
            "RULER_USES_BRONZEMAN": (
                "This ruler uses Bronzeman mode.", "Ce dirigeant utilise le mode Bronzeman.",
                "Dieser Herrscher spielt im Bronzeman-Modus.", "Este gobernante usa el modo Bronzeman.",
            ),
            "BRONZEMAN_DISABLED_ACHIEVEMENTS_WARNING": (
                "Bronzeman mode is active.", "Le mode Bronzeman est actif.",
                "Der Bronzeman-Modus ist aktiv.", "El modo Bronzeman está activo.",
            ),
        },
    ),
}
PATCHES = (
    # Preferred PE virtual addresses for the exact executable above.
    (0x14080898B, "0f 94 c1", "b1 01 90"),  # Set only the achievement checksum flag.
    (0x140737E0C, "74 2a", "90 90"),  # Keep evaluating the achievement status.
    (0x140737E55, "74 28", "90 90"),  # Same for the other status callback.
    (0x14073BC34, "75 32", "eb 32"),  # Tooltip uses the patched eligibility callback.
    (0x14073BCB9, "48 c7 44 24 68 0f 00 00 00", "e9 fd 00 00 00 90 90 90 90"),  # Skip the Ironman row.
)


def read_verified(path, expected_hash):
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != expected_hash:
        raise ValueError(f"Unsupported input: {path}")
    return data


def patch_executable(data):
    patched = bytearray(data)
    for address, original_hex, replacement_hex in PATCHES:
        # .text starts at VA 0x140001000 and raw file offset 0x400.
        offset = address - 0x140001000 + 0x400
        original = bytes.fromhex(original_hex)
        replacement = bytes.fromhex(replacement_hex)
        if patched[offset:offset + len(original)] != original:
            raise ValueError(f"Original bytes differ at {address:#x}")
        patched[offset:offset + len(original)] = replacement
    return patched


def patch_achievements(data):
    patched, count = re.subn(
        rb"(?m)^([ \t]*)is_ironman([ \t]*=[ \t]*yes[ \t]*\r?)$",
        rb"\1always\2",
        data,
    )
    if count != 161:
        raise ValueError(f"Expected 161 Ironman predicates, found {count}")
    return patched


def patch_ironman_tooltip(data):
    key = b"IRONMAN_MODE_DESC;"
    rows = data.splitlines(keepends=True)
    matches = [index for index, row in enumerate(rows) if row.startswith(key)]
    if len(matches) != 1:
        raise ValueError("Expected one Ironman tooltip localisation row")
    index = matches[0]
    columns = rows[index].split(b";")
    # These four translations end with the Steam requirement sentence.
    for column, separator in ((1, b". "), (2, rb".\n"), (3, b". "), (5, b". ")):
        description, _, requirement = columns[column].rpartition(separator)
        if not description or b"Steam" not in requirement:
            raise ValueError("Unexpected Ironman tooltip translation")
        columns[column] = description + b"."
    rows[index] = b";".join(columns)
    return b"".join(rows)


def patch_continue_dialog(data):
    matches = [row for row in data.splitlines(keepends=True)
               if row.startswith(b"CONTINUE_FAILED_DESC;")]
    if len(matches) != 1:
        raise ValueError("Expected one Continue failed localisation row")
    original = matches[0]
    columns = original.split(b";")
    for column in (1, 2, 3, 5):
        lines = columns[column].split(rb"\n")
        # Keep the introduction and the first four troubleshooting reasons.
        if len(lines) != 8 or b"ironman" not in lines[5].lower() or lines[6]:
            raise ValueError("Unexpected Continue failed translation")
        columns[column] = rb"\n".join(lines[:5])
    return data.replace(original, b";".join(columns), 1)


def patch_achievement_text(data, replacements):
    pending = {key.encode("ascii"): translations for key, translations in replacements.items()}
    rows = data.splitlines(keepends=True)
    for index, row in enumerate(rows):
        key = row.partition(b";")[0]
        translations = pending.pop(key, None)
        if translations is None:
            continue
        columns = row.split(b";")
        for column, translation in zip((1, 2, 3, 5), translations):
            columns[column] = translation.encode("cp1252")
        rows[index] = b";".join(columns)
    if pending:
        raise ValueError(f"Missing achievement localisation keys: {list(pending)}")
    return b"".join(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Original CK2 game directory")
    parser.add_argument("destination", type=Path, help="New directory outside the original")
    parser.add_argument(
        "--shared-saves", type=Path,
        help="Existing external directory to use for local saves",
    )
    args = parser.parse_args()
    try:
        source = args.source.resolve(strict=True)
        destination = args.destination.resolve()
        if args.destination.is_symlink() or destination.exists() or source in destination.parents:
            raise ValueError("Destination must be a new directory outside the original")
        shared_saves = None
        if args.shared_saves is not None:
            shared_saves = args.shared_saves.resolve(strict=True)
            if not shared_saves.is_dir():
                raise ValueError("Shared saves must be a directory")
            if shared_saves == source or source in shared_saves.parents:
                raise ValueError("Choose a shared save directory outside the source installation")
            if shared_saves in destination.parents:
                raise ValueError("Choose a destination outside the shared save directory")
        exe = "CK2game.exe"
        script = Path("common/achievements.txt")
        executable = patch_executable(read_verified(source / exe, EXE_HASH))
        achievements = patch_achievements(read_verified(source / script, SCRIPT_HASH))
        tooltip = patch_ironman_tooltip(read_verified(source / IRONMAN_TOOLTIP, IRONMAN_TOOLTIP_HASH))
        achievement_text = []
        for path, (digest, replacements) in ACHIEVEMENT_TEXT.items():
            data = read_verified(source / path, digest)
            if path == CONTINUE_DIALOG:
                data = patch_continue_dialog(data)
            achievement_text.append((path, patch_achievement_text(data, replacements)))
        menu = Path("interface/menubar.gui")
        menu_data = load_save.patch_menu(read_verified(source / menu, load_save.MENU_HASH))
        load_save.patch_executable(executable)
        localisation = Path("localisation/ck2_engine_load_save.csv")
        if (source / localisation).exists():
            raise ValueError("The source already contains Engine Patch localisation")
        destination.mkdir()
        try:
            if os.name == "posix" and shutil.which("cp") and os.uname().sysname == "Linux":
                subprocess.run(
                    ["cp", "-a", "--reflink=auto", "--", f"{source}/.", destination],
                    check=True,
                )
            else:
                shutil.copytree(source, destination, symlinks=True, dirs_exist_ok=True)
            overrides = (
                (exe, executable),
                (script, achievements),
                (menu, menu_data),
                (IRONMAN_TOOLTIP, tooltip),
                *achievement_text,
            )
            for relative, data in overrides:
                target = destination / relative
                if target.is_symlink() or not target.resolve().is_relative_to(destination):
                    raise ValueError(f"Unexpected symlink at {target}")
                temporary = target.with_name(target.name + ".ck2patch")
                with temporary.open("xb") as output:
                    output.write(data)
                temporary.chmod(target.stat().st_mode & 0o777)
                temporary.replace(target)
            text_path = destination / localisation
            if not text_path.resolve().is_relative_to(destination):
                raise ValueError(f"Unexpected symlink at {text_path}")
            with text_path.open("xb") as output:
                output.write(load_save.LOCALISATION)
            userdir = destination / "userdir.txt"
            userdir.unlink(missing_ok=True)
            profile = destination / "ck2-patch-profile"
            profile.mkdir()
            if shared_saves is not None:
                (profile / "save games").symlink_to(shared_saves, target_is_directory=True)
            userdir.write_bytes(b"./ck2-patch-profile/")
        except BaseException:
            shutil.rmtree(destination)
            raise
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"Error: {error}\n")
    print(destination)


if __name__ == "__main__":
    main()
