"""Pause-menu Load Save patch for the hash-verified CK2 3.3.5.1 Windows PE."""

import hashlib
import re
from struct import pack

MENU_HASH = "79d72f06153ed26ce17a76397653f6969823cfc6e63e1233ad61b494aea797af"
LOCALISATION = (
    b"#CODE;ENGLISH;FRENCH;GERMAN;;SPANISH;;;;;;;;;x\r\n"
    b"CK2_ENGINE_LOAD_SAVE;Load Save;Charger la partie;Spiel laden;;Cargar partida;;;;;;;;;x\r\n"
)

CODE_CAVE = 0x140F99202
TEXT_FILE_DELTA = 0x140000C00
# Assembled from load_save_x64.s with .text at CODE_CAVE,
# .loadpath at 0x14067DED8, and .earlyload at 0x14068DC47. The direct path uses CK2's startup save
# consumer after campaign teardown, before the frontend can draw its menu.
STUBS = bytes.fromhex(
    "c6 05 6b 2b 8c 00 01 c6 81 d8 41 00 00 00 eb 07 "
    "c6 05 5b 2b 8c 00 00 48 83 25 57 2b 8c 00 00 48 "
    "89 4c 24 08 e9 7a 23 6e ff e9 c3 4a 6f ff 66 83 "
    "3d 3c 2b 8c 00 01 75 61 48 83 25 36 2b 8c 00 00 "
    "4d 85 c0 74 54 49 81 f8 eb 00 00 00 77 4b 4c 8d "
    "15 29 2b 8c 00 31 c0 44 8a 0c 02 41 80 f9 2f 74 "
    "38 41 80 f9 5c 74 32 45 88 0c 02 ff c0 4c 39 c0 "
    "72 e5 83 f8 04 72 0b 41 81 7c 02 fc 2e 63 6b 32 "
    "74 0b 41 c7 04 02 2e 63 6b 32 83 c0 04 41 c6 04 "
    "02 00 48 89 05 dd 2a 8c 00 e9 a0 7f 11 ff 80 3d "
    "cd 2a 8c 00 01 75 26 80 3d c5 2a 8c 00 02 74 18 "
    "48 83 3d be 2a 8c 00 00 74 0e e8 17 4c 6e ff 85 "
    "c0 74 05 e8 4d 4a 6f ff e9 44 8c 6e ff 48 83 7d "
    "b0 00 74 f4 e9 71 86 6e ff 80 3d 93 2a 8c 00 01 "
    "75 31 c6 05 8a 2a 8c 00 00 4c 8b 05 86 2a 8c 00 "
    "48 83 25 7e 2a 8c 00 00 48 8d 0d 67 88 7d 00 48 "
    "8d 15 78 2b 8c 00 e8 33 7f 11 ff 4c 89 f1 e8 a3 "
    "4c 6e ff 4c 8d 9c 24 50 02 00 00 e9 2c 6b 77 ff "
    "80 3d 4b 2a 8c 00 01 74 36 48 89 e0 57 48 81 ec "
    "80 00 00 00 e9 b0 79 6e ff 80 3d 32 2a 8c 00 01 "
    "74 1d 53 48 83 ec 20 e9 68 50 6d ff 80 3d 1f 2a "
    "8c 00 01 74 0a 53 48 83 ec 20 e9 25 50 6d ff c3 "
    "48 83 ec 50 48 c7 44 24 20 73 61 76 65 48 c7 44 "
    "24 30 04 00 00 00 48 c7 44 24 38 0f 00 00 00 48 "
    "8d 54 24 20 4c 89 f1 48 8b 01 ff 50 78 48 85 c0 "
    "74 40 48 89 44 24 40 48 8d 15 f3 4b 6e ff 80 3d "
    "cd 29 8c 00 01 75 07 48 8d 15 30 ff 0e 00 48 8d "
    "4c 24 20 e8 e6 02 70 ff 48 89 c2 48 8b 4c 24 40 "
    "45 31 c0 e8 36 de d3 ff 48 8d 4c 24 20 e8 5c 60 "
    "11 ff 48 83 c4 50 49 8b 8c 24 18 66 00 00 e9 1f "
    "3f 6e ff "
)

PATH_STUB = bytes.fromhex(
    "4c 8d 15 a1 df 1d 01 4d 8b 8d 60 69 00 00 45 31 "
    "c0 4d 85 c9 74 65 4d 8b 59 10 4c 89 ca 49 83 79 "
    "18 10 49 0f 43 11 31 c0 4c 39 d8 73 2d 8a 0c 02 "
    "ff c0 80 f9 5c 75 02 b1 2f 80 f9 2f 75 0d 45 85 "
    "c0 74 e5 43 80 7c 02 ff 2f 74 dd 41 80 f8 ff 73 "
    "67 43 88 0c 02 41 ff c0 eb ce 45 85 c0 74 16 43 "
    "80 7c 02 ff 2f 74 0e 41 80 f8 ff 73 4b 43 c6 04 "
    "02 2f 41 ff c0 4d 8b 49 28 eb 96 4c 8b 1d 1e de "
    "1d 01 4b 8d 04 18 48 3d ff 00 00 00 77 2a 48 8d "
    "15 13 de 1d 01 31 c0 8a 0c 02 43 88 0c 02 41 ff "
    "c0 ff c0 4c 39 d8 72 ef 43 c6 04 02 00 4c 89 05 "
    "ec dd 1d 01 44 89 c0 c3 31 c0 c3 4d 45 4e 55 5f "
    "42 41 52 5f 53 41 56 45 00 80 3d ce dd 1d 01 01 "
    "0f 84 19 1b 09 00 e8 5d 20 5d 00 e9 b8 19 09 00 "
    "48 83 ec 28 e8 5f 3c 09 00 c6 05 ae dd 1d 01 00 "
    "48 83 c4 28 c3 80 3d a2 dd 1d 01 01 0f 85 f6 d0 "
    "18 00 48 89 ca 49 8b 8c 24 e0 57 00 00 41 b0 01 "
    "e9 e3 b5 18 00 80 3d 82 dd 1d 01 01 75 01 c3 48 "
    "83 ec 28 48 8b 01 e9 54 7c 60 00 40 84 ff 0f 84 "
    "f6 3c fb ff 80 3d 63 dd 1d 01 01 0f 85 0f 3b fb "
    "ff 48 83 3d c7 8c fe 00 00 0f 84 42 3d fb ff e9 "
    "fc 3a fb ff "
)

EARLY_LOAD_STUB = bytes.fromhex(
    "48 83 ec 68 4c 89 6c 24 50 49 89 cd 49 8b 8d e0 "
    "57 00 00 48 8b 81 c0 03 00 00 48 89 44 24 40 48 "
    "8b 81 c8 03 00 00 48 89 44 24 48 48 83 a1 c0 03 "
    "00 00 00 48 83 a1 c8 03 00 00 00 49 8b 95 10 03 "
    "00 00 41 b0 01 e8 6f bd 17 00 48 8d 4c 24 20 48 "
    "8d 15 7b f9 9c 00 e8 fe b9 00 00 48 89 c2 49 8b "
    "8d e0 57 00 00 41 b0 01 e8 1c b9 17 00 48 8d 4c "
    "24 20 e8 72 17 a2 ff e8 8d be 17 00 49 8b 8d e0 "
    "57 00 00 48 8b 44 24 40 48 89 81 c0 03 00 00 48 "
    "8b 44 24 48 48 89 81 c8 03 00 00 4c 89 e9 4c 8b "
    "6c 24 50 48 83 c4 68 e9 8d dd fb ff 80 3d 7b e0 "
    "1c 01 02 75 07 c6 05 72 e0 1c 01 00 c6 05 6a e0 "
    "1c 01 00 48 89 e0 57 48 83 ec 70 e9 81 d6 fe ff "
    "48 83 ec 28 ff 15 77 c8 90 00 05 ba 00 00 00 89 "
    "05 54 e2 1c 01 c6 05 42 e0 1c 01 02 48 83 c4 28 "
    "c3 80 3d 36 e0 1c 01 02 75 33 ff 15 51 c8 90 00 "
    "2b 05 33 e2 1c 01 78 25 c6 05 1e e0 1c 01 00 c6 "
    "05 18 e0 1c 01 01 c6 05 12 e0 1c 01 01 48 83 25 "
    "74 8f fd 00 00 4c 89 e1 e8 d3 fe ff ff 41 80 bc "
    "24 11 66 00 00 00 e9 d2 59 fc ff "
)

# Patch sites and targets for the hash-verified Windows executable.
HOOKS = (
    (0x14067DED0, "488bc455488d68a1", 0xE9, 0x140F99202),  # Load Save click
    (0x14067B5A0, "48894c2408", 0xE9, 0x140F99212),       # Stock Save Game
    (0x14067B390, "488bc4574883ec70", 0xE9, 0x140F9922B),  # Close picker
    (0x140680B01, "e83a07a3ff", 0xE8, 0x140F99230),       # Save row selection
    (0x140681941, "48837db0000f84c7050000", 0xE9, 0x140F992A0),  # Submit
    (0x14070FE46, "4c8d9c2450020000", 0xE9, 0x140F992DB),   # Resume after teardown
    (0x140680CE0, "488bc4574881ec80000000", 0xE9, 0x140F99322),  # Delete
    (0x14066E3B0, "40534883ec20", 0xE9, 0x140F9933B),      # Cloud tab
    (0x14066E380, "40534883ec20", 0xE9, 0x140F9934E),      # Local tab
    (0x14067D2FC, "498b8c2418660000", 0xE9, 0x140F99362),  # Button caption
    (0x14066E376, "e925d20000", 0xE9, 0x140F99219),  # Parent folder
    (0x140680CD2, "e9c9a8ffff", 0xE9, 0x140F99219),  # Enter folder
    (0x14065374B, "4180bc241166000000", 0xE9, 0x14068DD38),  # Advance queued load after the click cue
    (0x140C85C50, "4883ec28488b01", 0xE9, 0x14067DFED),  # Keep the current track on campaign teardown
    (0x140631B1F, "4084ff0f84da010000", 0xE9, 0x14067E003),  # Wait for the full loading window before drawing
    (0x140661B15, "e8b6951a00", 0xE8, 0x14067DFCD),  # Use stock tip panel for saved-game progress
    (0x14070F96B, "e8a0065400", 0xE9, 0x14067DFA1),  # Keep campaign music during frontend setup
    # Keep the former Export Game button visible and enabled without its DLC.
    (0x14068DC40, "0fb60dc0590e01", 0xE9, 0x14068DDB2),
    (0x14068DDC8, "488d8d98170000e85c16a2ff", 0xE9, 0x14068DDD4),
    (0x140A9DE75, "0f849c010000", 0xE9, 0x140A9E017),
)


def replace(data, offset, original, replacement):
    if len(original) != len(replacement) or data[offset:offset + len(original)] != original:
        raise ValueError(f"Unexpected Load Save patch bytes at file offset {offset:#x}")
    data[offset:offset + len(original)] = replacement


def patch_executable(data):
    # Map the injected code and extend .data zero-fill for the selected name and relative path.
    replace(data, 0x278, pack("<I", 0xF98202), pack("<I", 0xF98202 + len(STUBS)))
    replace(data, 0x2C8, pack("<I", 0x48FD74), pack("<I", 0x48FF88))
    replace(data, CODE_CAVE - TEXT_FILE_DELTA, bytes(len(STUBS)), STUBS)

    # The Export handler now branches to open_load at its entry.
    path_offset = 0x14067DED8 - TEXT_FILE_DELTA
    original_path_code = data[path_offset:path_offset + len(PATH_STUB)]
    if hashlib.sha256(original_path_code).hexdigest() != "cd22044b3c4116df0b3bc6ca93a9121ab85f849a974cb22ac7da30b481a33b2c":
        raise ValueError("Unexpected Export handler bytes")
    replace(data, path_offset, original_path_code, PATH_STUB)

    # This portion of the converter availability check is bypassed below.
    early_offset = 0x14068DC47 - TEXT_FILE_DELTA
    original_early_code = bytes.fromhex(
        "84 c9 0f 84 98 00 00 00 80 bb 48 ff ff ff 00 74 "
        "75 49 8b 04 24 48 8b 90 e0 00 00 00 48 8d 05 76 "
        "16 fc ff 48 3b d0 75 11 49 8b 84 24 68 03 00 00 "
        "48 8b 80 18 02 00 00 eb 0c 49 8b cc ff d2 0f b6 "
        "0d 7b 59 0e 01 80 78 5d 00 75 3b 84 c9 74 51 48 "
        "8b 07 48 8b 90 e8 01 00 00 48 8d 0d e9 8d a5 00 "
        "48 3b c1 48 8b cf 75 17 c7 87 8c 00 00 00 03 00 "
        "00 00 33 d2 ff 90 a8 02 00 00 e9 0e 01 00 00 ff "
        "d2 e9 07 01 00 00 48 8d 4f 60 48 8d 93 08 07 00 "
        "00 48 8b 01 4c 8b 40 08 41 ff d0 e9 ed 00 00 00 "
        "48 8d 15 be 06 9d 00 48 8d 8d 58 17 00 00 e8 66 "
        "30 a2 ff 48 8d 95 58 17 00 00 48 8b 0d e0 98 0d "
        "01 e8 43 60 5e 00 48 8b f0 48 8d 8d 58 17 00 00 "
        "e8 14 17 a2 ff 48 85 f6 74 0f 48 83 be f0 00 00 "
        "00 00 74 05 40 b6 01 eb 03 40 32 f6 48 8b 57 30 "
        "48 81 c2 30 01 00 00 48 8d 8d 98 17 00 00 e8 96 "
        "16 a2 ff 90 48 8d 05 9e 14 9d 00 48 8d 15 a7 14 "
        "9d 00 40 84 f6 48 0f 45 d0 48 8d 8d 78 17 00 00 "
        "e8 f4 2f a2 ff 90 4c 8d 85 78 17 00 00 48 8d 95 "
        "38 1b 00 00 48 8d 8d 98 17 00 00 "
    )
    replace(data, early_offset, original_early_code, EARLY_LOAD_STUB)

    for site, original, opcode, target in HOOKS:
        expected = bytes.fromhex(original)
        branch = bytes((opcode,)) + pack("<i", target - site - 5)
        replace(data, site - TEXT_FILE_DELTA, expected, branch.ljust(len(expected), b"\x90"))


def patch_menu(data):
    # Move the existing widget so CK2's binary callback still finds it by name.
    button = re.compile(
        rb'(?m)^	{3}guiButtonType = \{\r\n'
        rb'	{4}name = "(menu_[a-z_]+_button)"\r\n'
        rb'.*?^	{3}\}\r\n',
        re.DOTALL,
    )
    panel_start = data.index(b'name ="menu_panel"')
    panel_end = data.index(b'### banner_extension', panel_start)
    panel = data[panel_start:panel_end]
    buttons = {match[1]: match[0] for match in button.finditer(panel)}

    load = buttons[b"menu_convert_button"]
    panel = panel.replace(load, b"", 1)
    load = load.replace(b'y = 335', b'y = 160', 1)
    load = load.replace(b'"MENU_BAR_GAME_CONVERT"', b'"CK2_ENGINE_LOAD_SAVE"', 1)
    load = load.replace(b'				pdx_tooltip = "MENU_BAR_GAME_CONVERT_DEL"\r\n', b"", 1)

    for name in (b"options", b"message", b"resign", b"quit", b"save_and_exit"):
        original = buttons[b"menu_" + name + b"_button"]
        moved = re.sub(rb'y = ([0-9]+)', lambda match: b'y = %d' % (int(match[1]) + 35),
                       original, count=1)
        if name == b"options":
            moved = load + b"\r\n" + moved
        panel = panel.replace(original, moved, 1)

    # Reuse the same cue as the pause menu's Save Game and Game Options.
    suffix = data[panel_end:]
    confirm = b'buttonText = "MENU_BAR_SAVE"\r\n'
    if suffix.count(confirm) != 1:
        raise ValueError("Expected one save picker confirmation button")
    suffix = suffix.replace(confirm, confirm + b"\t\t\t\tclicksound = generic_click_04\r\n")
    return data[:panel_start] + panel + suffix
