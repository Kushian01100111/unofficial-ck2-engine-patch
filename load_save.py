"""Pause-menu Load Save patch for the hash-verified CK2 3.3.5.1 Windows PE."""

import re
from struct import pack

MENU_HASH = "79d72f06153ed26ce17a76397653f6969823cfc6e63e1233ad61b494aea797af"
LOCALISATION = (
    b"#CODE;ENGLISH;FRENCH;GERMAN;;SPANISH;;;;;;;;;x\r\n"
    b"CK2_ENGINE_LOAD_SAVE;Load Save;Charger la partie;Spiel laden;;Cargar partida;;;;;;;;;x\r\n"
)

CODE_CAVE = 0x140F99202
TEXT_FILE_DELTA = 0x140000C00
# Assembled from load_save_x64.s. The direct path uses CK2's startup save
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
    "8c 00 01 75 25 48 83 3d b9 2a 8c 00 00 74 16 c6 "
    "05 ac 2a 8c 00 00 c6 05 a6 2a 8c 00 01 4c 89 e9 "
    "e8 a9 27 6b ff e9 37 8c 6e ff 48 83 7d b0 00 74 "
    "f4 e9 64 86 6e ff 80 3d 86 2a 8c 00 01 75 31 c6 "
    "05 7d 2a 8c 00 00 4c 8b 05 79 2a 8c 00 48 83 25 "
    "71 2a 8c 00 00 48 8d 0d 5a 88 7d 00 48 8d 15 6b "
    "2a 8c 00 e8 26 7f 11 ff 4c 89 f1 e8 fe 88 77 ff "
    "4c 8d 9c 24 50 02 00 00 e9 1f 6b 77 ff 80 3d 3e "
    "2a 8c 00 01 74 36 48 89 e0 57 48 81 ec 80 00 00 "
    "00 e9 a3 79 6e ff 80 3d 25 2a 8c 00 01 74 1d 53 "
    "48 83 ec 20 e9 5b 50 6d ff 80 3d 12 2a 8c 00 01 "
    "74 0a 53 48 83 ec 20 e9 18 50 6d ff c3 48 83 ec "
    "50 48 c7 44 24 20 73 61 76 65 48 c7 44 24 30 04 "
    "00 00 00 48 c7 44 24 38 0f 00 00 00 48 8d 54 24 "
    "20 4c 89 f1 48 8b 01 ff 50 78 48 85 c0 74 40 48 "
    "89 44 24 40 48 8d 15 45 00 00 00 80 3d c0 29 8c "
    "00 01 75 07 48 8d 15 23 ff 0e 00 48 8d 4c 24 20 "
    "e8 d9 02 70 ff 48 89 c2 48 8b 4c 24 40 45 31 c0 "
    "e8 29 de d3 ff 48 8d 4c 24 20 e8 4f 60 11 ff 48 "
    "83 c4 50 49 8b 8c 24 18 66 00 00 e9 12 3f 6e ff "
    "4d 45 4e 55 5f 42 41 52 5f 53 41 56 45 00 "
)

# Patch sites and targets for the hash-verified Windows executable.
HOOKS = (
    (0x14067DED0, "488bc455488d68a1", 0xE9, 0x140F99202),  # Load Save click
    (0x14067B5A0, "48894c2408", 0xE9, 0x140F99212),       # Stock Save Game
    (0x14067B390, "488bc4574883ec70", 0xE9, 0x140F9922B),  # Close picker
    (0x140680B01, "e83a07a3ff", 0xE8, 0x140F9923F),       # Save row selection
    (0x140681941, "48837db0000f84c7050000", 0xE9, 0x140F992AE),  # Submit
    (0x14070FE46, "4c8d9c2450020000", 0xE9, 0x140F992E8),   # Resume after teardown
    (0x140680CE0, "488bc4574881ec80000000", 0xE9, 0x140F9932F),  # Delete
    (0x14066E3B0, "40534883ec20", 0xE9, 0x140F99348),      # Cloud tab
    (0x14066E380, "40534883ec20", 0xE9, 0x140F9935B),      # Local tab
    (0x14067D2FC, "498b8c2418660000", 0xE9, 0x140F9936F),  # Button caption
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
    # Map the injected code and extend .data zero-fill for the selected filename.
    replace(data, 0x278, pack("<I", 0xF98202), pack("<I", 0xF98202 + len(STUBS)))
    replace(data, 0x2C8, pack("<I", 0x48FD74), pack("<I", 0x48FE80))
    replace(data, CODE_CAVE - TEXT_FILE_DELTA, bytes(len(STUBS)), STUBS)

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
