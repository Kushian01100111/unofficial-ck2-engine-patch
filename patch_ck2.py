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
PATCHES = (
    # Preferred PE virtual addresses for the exact executable above.
    (0x14080898B, "0f 94 c1", "b1 01 90"),  # Set only the achievement checksum flag.
    (0x140737E0C, "74 2a", "90 90"),  # Keep evaluating the achievement status.
    (0x140737E55, "74 28", "90 90"),  # Same for the other status callback.
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
            for relative, data in [(exe, executable), (script, achievements), (menu, menu_data)]:
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
