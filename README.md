# Unofficial CK2 Engine Patch

> **Note:** Developed with AI assistance. This project does not distribute *Crusader Kings II* binaries or the Steamworks SDK.

A Unofficial patch for the game Crusader Kings II. 

## Installation Requirements
Python 3.9+


```sh
python3 patch_ck2.py "/absolute/path/to/Crusader Kings II" "/absolute/path/to/CK2-patched"
```

On Linux with Proton, close CK2, save any previous launch options, and set these options in **Steam → Crusader Kings II → Properties → General**:

```text
"/absolute/path/to/launch_ck2.sh" "/absolute/path/to/CK2-patched" %command%
```

On Windows, run the installer with `py -3 patch_ck2.py "C:\path\to\Crusader Kings II" "C:\path\to\CK2-patched"`. For an initial test, open Steam, switch to the copy's directory, and run the copied `CK2game.exe` from there. Confirm CK2 reports Steam active before testing unlocks. Windows launch via the copied executable is a test procedure. Linux's Bash launcher applies only to Proton. To revert, launch the original, restoring prior Steam launch options on Linux.

To launch directly into a specific local save, append CK2's stock startup
arguments after `%command%`. Use the filename from the patched profile's
`save games` directory. Omit the arguments to open the launcher and manage
mods or DLC.

```text
"/absolute/path/to/launch_ck2.sh" "/absolute/path/to/CK2-patched" %command% -skiplauncher "-start_save=My Save.ck2"
```

In one matched offline Proton run on the same local save, the game handed
control to the player after 29.8 seconds with Launcher Continue and 19.7
seconds with direct startup. This option applies to launching CK2. A faster
in-game save load has yet to be verified.

## Load Save from the pause menu

**Load Save** appears directly below **Save Game** in the pause menu. It opens
the stock save list over the campaign map. Select a local save and click **Load**
to replace the current campaign, or click **Back** to keep playing. Loading
discards unsaved progress. The picker uses the selected row and ignores edits
to the filename field. Delete and tab actions are disabled while loading.

The earlier implementation called the main-menu **Load Game** action after
campaign teardown. That action opened a browser and expected a player to
finish character setup. The patch now hands the selected path, relative to the local save directory, to CK2's
stock startup-save loader at the end of engine initialization. On a successful
load, the picker is followed by CK2's loading screen and then gameplay. CK2
still validates and deserializes the file and restores the saved player.

The **Loading game** stage reuses CK2's framed loading artwork, progress bar,
and localized gameplay tips. During a pause-menu load, the SDL music channel
keeps its current playback position and the frontend skips restarting the
title theme. An offline Proton test matched the same track to consecutive
positions in the original audio before, during, and after loading.
**Load Save** and the picker confirmation use the same click cue as **Save
Game** and **Game Options**. On confirmation, the patch presents a native
loading frame before the campaign teardown call. The renderer temporarily draws
only the loading window's tree, keeping the outgoing ruler portrait, army
markers, and minimap off the artwork. The patch releases the temporary window
and restores the campaign render list before the stock loader takes over.

In an offline single-player Proton 10.0-4 test, a compressed save created on
27 September 1066 was reloaded after advancing to 6 October. CK2 restored the
saved date, Duke William of Normandy, the map, and the saved resource totals.
The recorded transition showed no main menu or character selection screen.
A second test loaded an uncompressed save while playing as a different ruler.
CK2 returned control to William, and unpausing advanced the restored campaign.
A separate Proton test used Launcher Continue with a save two folders deep,
then switched between that save and a root-level save using pause-menu
**Load Save**. Both returned to gameplay on their saved dates. The picker
kept its **Load** caption when moving into a folder and back to its parent.
All copied fixture files retained their hashes. The tested workflow uses
local saves in the profile's `save games` folder. Steam Cloud, multiplayer,
Ironman, and native Windows gameplay were outside this test. The isolated
WineD3D test renderer showed terrain shader artifacts during normal play as
well as after loading.

To upgrade an existing patched installation, build another copy from the
original Steam game directory. Reuse your existing shared save directory or
import a copy of your local saves using the instructions below. Point the
Proton launcher at the new copy once you are ready to switch.

The installer embeds the assembled Windows x64 stubs and requires only Python.
For changes to `load_save_x64.s`, rebuild them with GNU binutils and verify the
hook addresses against the symbols from `nm -n`.

```sh
as --64 -o /tmp/ck2-load-save.o load_save_x64.s
ld -Ttext 0x140f99202 -e open_load -o /tmp/ck2-load-save.elf /tmp/ck2-load-save.o
objcopy -O binary -j .text /tmp/ck2-load-save.elf /tmp/ck2-load-save.bin
nm -n /tmp/ck2-load-save.elf
```

## Shared local saves

By default CK2 writes into `ck2-patch-profile/save games` inside each copy. For one save directory across multiple patched installations, create an external folder on a volume each OS can access. Build each copy with `--shared-saves` pointing to that same folder using its absolute path on the current OS. The private game profile links only its `save games` folder to the shared directory. Other settings remain local. In the Proton test, a copied save loaded through this link and a new quicksave appeared in the shared directory. Windows directory symlinks require a filesystem that supports them and permission to create them, such as Developer Mode with a supported Windows setup.

With CK2 closed, copy existing local saves into the shared folder:

```sh
python3 import_saves.py "/path/to/old/save games" "/path/to/shared/CK2 saves"
```

The importer copies regular `.ck2` files and stops on name collisions. It leaves the source saves in place. Keep a backup, use one CK2 instance at a time, and test with the same CK2 version, DLC and mods. A common directory cannot make incompatible save formats or mod states load. Mods that redirect the entire CK2 user directory may need a separate setup. Steam Cloud is separate from this local directory. Restore the old launch path to use the old profile again.

## Achievements

The achievement eligibility changes touch seven bytes across three sites in the supported executable. They let achievement status checks continue with Ironman off and allow the achievement-specific checksum check to pass. The copied `common/achievements.txt` removes 161 scripted Ironman prerequisites. Gameplay triggers, save checks, and CK2's own Steam reporting remain in place. The Game Rules achievement tooltip uses the same current eligibility callback as its status label and omits the Ironman requirement. A mod that replaces the achievement script can supersede these changes.

Verify by playing with a real mod and Ironman disabled, saving and reloading, then meeting the ordinary gameplay condition for an achievement the account has yet to unlock. Check that Steam records it after restarting. A menu indicator is a separate observation. This repository does not distribute CK2 binaries or the Steamworks SDK.

## Companion project

[Unofficial CK2 Common Patch](https://github.com/londonhargrove/unofficial-ck2-common-patch) handles loose-file bugs, gameplay improvements, and content. Its new repository is a separate publication target.

## Credits

The patcher and launcher were written for this project. [JihadJackass’s MAP project](https://github.com/JihadJackass/CK2-Modded-Achievement-Patcher-MAP/tree/83c43104d5cbc950e691e0f3110a91c60898feb7) provided signature references used to identify code in the installed game. The project contains its own static edits and no MAP trampoline implementation. An older, matching CK2 executable and PDB helped identify functions. A [Steam discussion](https://steamcommunity.com/app/203770/discussions/0/3870336629227749731/) provided background.
