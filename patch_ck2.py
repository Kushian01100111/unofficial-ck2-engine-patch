#!/usr/bin/env python3
"""Build a separate experimental CK2 3.3.5.1 installation."""
import argparse
import hashlib
import os
from pathlib import Path
import re
import shutil
from struct import pack
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

# Assembled from multiplayer_x64.s. The Load Save patch already jumps over
# this part of the Export Game tooltip handler.
MP_ACHIEVEMENT_STUB = 0x140A9DE7B
MP_ACHIEVEMENT_CODE = bytes.fromhex(
    "83 3d 1a 8e bc 00 00 74 08 48 8d 05 43 00 00 00 c3 "
    "48 8b 05 d5 96 bc 00 48 8b 80 c0 01 00 00 48 8d 80 80 00 00 00 c3 "
    "80 7e 61 00 75 19 48 8d 05 1f 00 00 00 48 39 c7 75 0d "
    "e8 d3 ff ff ff 48 89 c7 e9 1d 28 61 ff "
    "4c 8b 45 47 49 83 f8 10 e9 7d 28 61 ff 43 4b 32 4d 50 76 31 00"
)
MP_SAVE_SALT_SITES = (
    # Choose the salt used by the save reader and each save writer.
    (0x1400B06CC, "48 8b 05 95 6e 5b 01 48 8b b8 c0 01 00 00 48 83 ef 80", "48 89 c7"),
    (0x1400B081D, "48 8b 05 44 6d 5b 01 48 8b 80 c0 01 00 00 48 83 e8 80", ""),
    (0x1401595B4, "48 8b 05 ad df 50 01 48 8b b8 c0 01 00 00 48 83 ef 80", "48 89 c7"),
    (0x140680FD1, "48 8b 05 90 65 fe 00 48 8b 98 c0 01 00 00 48 83 eb 80", "48 89 c3"),
    (0x1406811DD, "48 8b 05 84 63 fe 00 48 8b b8 c0 01 00 00 48 83 ef 80", "48 89 c7"),
    (0x1406815B1, "48 8b 05 b0 5f fe 00 48 8b b0 c0 01 00 00 48 83 ee 80", "48 89 c6"),
)
STOCK_MP_CHUNK_KIB = 32
FAST_MP_CHUNK_KIB = 44
MP_CHUNK_SIZES_KIB = (FAST_MP_CHUNK_KIB, 128, 256)

# Assembled from mp_transfer_x64.s. Larger blocks use the same wire format
# with bounded Base64 encoding work for each field.
MP_BLOB_WRITER_ADDRESS = 0x140C31E19
MP_BLOB_WRITER_CODE = bytes.fromhex(
    "b2 01 4c 89 f9 e8 cd f9 ff ff 49 8b 76 08 41 8b "
    "7e 14 4c 8d 6d 8c 45 31 e4 85 ff 7e 5f 41 b8 80 "
    "01 00 00 44 39 c7 44 0f 42 c7 4c 89 e9 4c 29 e1 "
    "48 89 f2 e8 df ab 13 00 44 29 e0 3d fe 01 00 00 "
    "bb fe 01 00 00 0f 42 d8 41 c6 44 1d 00 00 c7 45 "
    "88 0f 00 00 00 48 8d 55 88 4c 89 f9 e8 16 fb ff "
    "ff bb 7d 01 00 00 b8 80 01 00 00 45 85 e4 0f 45 "
    "d8 48 01 de 41 83 f4 02 29 df 7f a1 e9 85 04 00 00"
)


def read_verified(path, expected_hash):
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != expected_hash:
        raise ValueError(f"Unsupported input: {path}")
    return data


def replace_executable_bytes(data, address, original, replacement):
    offset = address - load_save.TEXT_FILE_DELTA
    if len(original) != len(replacement) or data[offset:offset + len(original)] != original:
        raise ValueError(f"Unexpected patch bytes at {address:#x}")
    data[offset:offset + len(original)] = replacement


def patch_executable(data, *, mp_download_chunk_kib=STOCK_MP_CHUNK_KIB):
    patched = bytearray(data)
    for address, original, replacement in PATCHES:
        replace_executable_bytes(patched, address, bytes.fromhex(original), bytes.fromhex(replacement))
    if mp_download_chunk_kib != STOCK_MP_CHUNK_KIB:
        if mp_download_chunk_kib not in MP_CHUNK_SIZES_KIB:
            raise ValueError(f"Unsupported multiplayer chunk size: {mp_download_chunk_kib} KiB")
        # The receiver uses the sender's chunk count and each block's actual length.
        instruction = bytes.fromhex("c7 41 58")
        replace_executable_bytes(
            patched, 0x140CC2DFC,
            instruction + pack("<I", STOCK_MP_CHUNK_KIB * 1024),
            instruction + pack("<I", mp_download_chunk_kib * 1024),
        )
    if mp_download_chunk_kib > FAST_MP_CHUNK_KIB:
        patch_mp_blob_writer(patched)
    return patched


def patch_mp_blob_writer(data):
    start = MP_BLOB_WRITER_ADDRESS - load_save.TEXT_FILE_DELTA
    end = start + len(MP_BLOB_WRITER_CODE)
    if hashlib.sha256(data[start:end]).hexdigest() != "a34680e57740ad16ace704aa622598b588959b46f8627de47a6497a86f3e472a":
        raise ValueError("Unexpected blob writer bytes")

    # This UNWIND_INFO belongs to the blob writer alone. The new body keeps
    # its prologue intact and has no C++ string temporaries to clean up.
    unwind_offset = 0x137FA28
    if data[unwind_offset:unwind_offset + 4] != bytes.fromhex("11 2e 0d 00"):
        raise ValueError("Unexpected blob writer unwind information")
    data[unwind_offset] = 0x01
    data[start:end] = MP_BLOB_WRITER_CODE


def patch_mp_achievements(data):
    offset = MP_ACHIEVEMENT_STUB - load_save.TEXT_FILE_DELTA
    original = data[offset:offset + len(MP_ACHIEVEMENT_CODE)]
    if hashlib.sha256(original).hexdigest() != "fd6c1813f2e9b8380086b3e51cb774e3f1140e840ef921fa8bfbf3201e66ea69":
        raise ValueError("Unexpected Export Game tooltip bytes for multiplayer achievements")
    data[offset:offset + len(original)] = MP_ACHIEVEMENT_CODE

    for address, original, result_move in MP_SAVE_SALT_SITES:
        expected = bytes.fromhex(original)
        call = b"\xe8" + pack("<i", MP_ACHIEVEMENT_STUB - address - 5)
        replacement = (call + bytes.fromhex(result_move)).ljust(len(expected), b"\x90")
        replace_executable_bytes(data, address, expected, replacement)

    # Keep the file object in RBX so a retry can reuse the stock digest code.
    replace_executable_bytes(data, 0x1400B0711, bytes.fromhex("0f b6 5e 61"), b"\x90" * 4)
    replace_executable_bytes(data, 0x1400B075D, bytes.fromhex("0f b6 c3"), bytes.fromhex("8a 46 61"))
    retry_jump = b"\xe9" + pack("<i", 0x140A9DEA2 - 0x1400B0743 - 5) + b"\x90" * 3
    replace_executable_bytes(data, 0x1400B0743, bytes.fromhex("4c 8b 45 47 49 83 f8 10"), retry_jump)


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
    parser.add_argument(
        "--mp-achievements", action="store_true",
        help="Preserve achievement eligibility across Steam accounts in multiplayer (experimental)",
    )
    transfer = parser.add_mutually_exclusive_group()
    transfer.add_argument(
        "--fast-mp-downloads", dest="mp_download_chunk_kib", action="store_const",
        const=FAST_MP_CHUNK_KIB, default=STOCK_MP_CHUNK_KIB,
        help=f"Send multiplayer saves in {FAST_MP_CHUNK_KIB} KiB blocks (experimental)",
    )
    transfer.add_argument(
        "--mp-download-chunk-kib", type=int, choices=MP_CHUNK_SIZES_KIB,
        help="Choose the multiplayer save transfer block size in KiB (experimental)",
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
        executable = patch_executable(
            read_verified(source / exe, EXE_HASH), mp_download_chunk_kib=args.mp_download_chunk_kib,
        )
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
        if args.mp_achievements:
            patch_mp_achievements(executable)
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
