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
# Assembled from load_save_x64.s with .text at CODE_CAVE and
# .loadpath at 0x14067DEE0. The direct path uses CK2's startup save
# consumer after campaign teardown, before the frontend can draw its menu.
STUBS = bytes.fromhex(
    "c6 05 6b 2b 8c 00 01 c6 81 d8 41 00 00 00 eb 07 "
    "c6 05 5b 2b 8c 00 00 48 83 25 57 2b 8c 00 00 48 "
    "89 4c 24 08 e9 7a 23 6e ff c6 05 42 2b 8c 00 00 "
    "48 89 e0 57 48 83 ec 70 e9 59 21 6e ff 80 3d 2e "
    "2b 8c 00 01 75 61 48 83 25 28 2b 8c 00 00 4d 85 "
    "c0 74 54 49 81 f8 eb 00 00 00 77 4b 4c 8d 15 1b "
    "2b 8c 00 31 c0 44 8a 0c 02 41 80 f9 2f 74 38 41 "
    "80 f9 5c 74 32 45 88 0c 02 ff c0 4c 39 c0 72 e5 "
    "83 f8 04 72 0b 41 81 7c 02 fc 2e 63 6b 32 74 0b "
    "41 c7 04 02 2e 63 6b 32 83 c0 04 41 c6 04 02 00 "
    "48 89 05 cf 2a 8c 00 e9 92 7f 11 ff 80 3d bf 2a "
    "8c 00 01 75 2e 48 83 3d b9 2a 8c 00 00 74 1f e8 "
    "1a 4c 6e ff 85 c0 74 16 c6 05 a3 2a 8c 00 00 c6 "
    "05 9d 2a 8c 00 01 4c 89 e9 e8 a0 27 6b ff e9 2e "
    "8c 6e ff 48 83 7d b0 00 74 f4 e9 5b 86 6e ff 80 "
    "3d 7d 2a 8c 00 01 75 31 c6 05 74 2a 8c 00 00 4c "
    "8b 05 70 2a 8c 00 48 83 25 68 2a 8c 00 00 48 8d "
    "0d 51 88 7d 00 48 8d 15 62 2b 8c 00 e8 1d 7f 11 "
    "ff 4c 89 f1 e8 cb 4c 6e ff 4c 8d 9c 24 50 02 00 "
    "00 e9 16 6b 77 ff 80 3d 35 2a 8c 00 01 74 36 48 "
    "89 e0 57 48 81 ec 80 00 00 00 e9 9a 79 6e ff 80 "
    "3d 1c 2a 8c 00 01 74 1d 53 48 83 ec 20 e9 52 50 "
    "6d ff 80 3d 09 2a 8c 00 01 74 0a 53 48 83 ec 20 "
    "e9 0f 50 6d ff c3 48 83 ec 50 48 c7 44 24 20 73 "
    "61 76 65 48 c7 44 24 30 04 00 00 00 48 c7 44 24 "
    "38 0f 00 00 00 48 8d 54 24 20 4c 89 f1 48 8b 01 "
    "ff 50 78 48 85 c0 74 40 48 89 44 24 40 48 8d 15 "
    "fc 4b 6e ff 80 3d b7 29 8c 00 01 75 07 48 8d 15 "
    "1a ff 0e 00 48 8d 4c 24 20 e8 d0 02 70 ff 48 89 "
    "c2 48 8b 4c 24 40 45 31 c0 e8 20 de d3 ff 48 8d "
    "4c 24 20 e8 46 60 11 ff 48 83 c4 50 49 8b 8c 24 "
    "18 66 00 00 e9 09 3f 6e ff "
)

PATH_STUB = bytes.fromhex(
    "4c 8d 15 99 df 1d 01 4d 8b 8d 60 69 00 00 45 31 "
    "c0 4d 85 c9 74 6b 4d 8b 59 10 4c 89 ca 49 83 79 "
    "18 10 49 0f 43 11 31 c0 4c 39 d8 73 30 8a 0c 02 "
    "ff c0 80 f9 5c 75 02 b1 2f 80 f9 2f 75 0d 45 85 "
    "c0 74 e5 43 80 7c 02 ff 2f 74 dd 41 81 f8 ff 00 "
    "00 00 73 7b 43 88 0c 02 41 ff c0 eb cb 45 85 c0 "
    "74 19 43 80 7c 02 ff 2f 74 11 41 81 f8 ff 00 00 "
    "00 73 5c 43 c6 04 02 2f 41 ff c0 4d 8b 49 28 eb "
    "90 4c 8b 1d 10 de 1d 01 4b 8d 04 18 48 3d ff 00 "
    "00 00 77 3b 48 8d 15 05 de 1d 01 31 c0 8a 0c 02 "
    "43 88 0c 02 41 ff c0 ff c0 4c 39 d8 72 ef 43 c6 "
    "04 02 00 4c 89 05 de dd 1d 01 c6 05 d5 dd 1d 01 "
    "01 48 83 25 37 8d fe 00 00 b8 01 00 00 00 c3 31 "
    "c0 c3 4d 45 4e 55 5f 42 41 52 5f 53 41 56 45 00 "
    "80 3d af dd 1d 01 01 75 03 41 b7 01 66 0f 2f 05 "
    "0c 8d fe 00 0f 86 75 b7 18 00 e9 c4 b6 18 00 80 "
    "3d 90 dd 1d 01 01 0f 84 db 1a 09 00 e8 1f 20 5d "
    "00 e9 7a 19 09 00 48 83 ec 28 e8 21 3c 09 00 c6 "
    "05 70 dd 1d 01 00 48 83 c4 28 c3 48 89 ca 49 8b "
    "8c 24 e0 57 00 00 41 b0 01 e9 b2 b5 18 00 80 3d "
    "51 dd 1d 01 01 75 01 c3 48 83 ec 28 48 8b 01 e9 "
    "23 7c 60 00 "
)

# Patch sites and targets for the hash-verified Windows executable.
HOOKS = (
    (0x14067DED0, "488bc455488d68a1", 0xE9, 0x140F99202),  # Load Save click
    (0x14067B5A0, "48894c2408", 0xE9, 0x140F99212),       # Stock Save Game
    (0x14067B390, "488bc4574883ec70", 0xE9, 0x140F9922B),  # Close picker
    (0x140680B01, "e83a07a3ff", 0xE8, 0x140F9923F),       # Save row selection
    (0x140681941, "48837db0000f84c7050000", 0xE9, 0x140F992AE),  # Submit
    (0x14070FE46, "4c8d9c2450020000", 0xE9, 0x140F992F1),   # Resume after teardown
    (0x140680CE0, "488bc4574881ec80000000", 0xE9, 0x140F99338),  # Delete
    (0x14066E3B0, "40534883ec20", 0xE9, 0x140F99351),      # Cloud tab
    (0x14066E380, "40534883ec20", 0xE9, 0x140F99364),      # Local tab
    (0x14067D2FC, "498b8c2418660000", 0xE9, 0x140F99378),  # Button caption
    (0x14066E376, "e925d20000", 0xE9, 0x140F99219),  # Parent folder
    (0x140680CD2, "e9c9a8ffff", 0xE9, 0x140F99219),  # Enter folder
    (0x140C85C50, "4883ec28488b01", 0xE9, 0x14067E01E),  # Keep the current track on campaign teardown
    (0x140661B15, "e8b6951a00", 0xE8, 0x14067E00B),  # Use stock tip panel for saved-game progress
    (0x14070F96B, "e8a0065400", 0xE9, 0x14067DFDF),  # Keep campaign music during frontend setup
    (0x140809695, "660f2f0543d6e5000f86ac000000", 0xE9, 0x14067DFC0),  # Refresh loading tips during pause-menu loads
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
    replace(data, 0x2C8, pack("<I", 0x48FD74), pack("<I", 0x48FF80))
    replace(data, CODE_CAVE - TEXT_FILE_DELTA, bytes(len(STUBS)), STUBS)

    # The Export handler now branches to open_load at its entry.
    path_offset = 0x14067DEE0 - TEXT_FILE_DELTA
    original_path_code = data[path_offset:path_offset + len(PATH_STUB)]
    if hashlib.sha256(original_path_code).hexdigest() != "cf5857ac3e6b476382a68362b49bd362a1ad5254a5df80f8b3104bc3b7f3e603":
        raise ValueError("Unexpected Export handler bytes")
    replace(data, path_offset, original_path_code, PATH_STUB)

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

    return data[:panel_start] + panel + data[panel_end:]
