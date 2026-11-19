# Unofficial CK2 Engine Patch

Developed by **London Hargrove**. An executable-level patch project for Crusader Kings II. This version implements achievement eligibility changes for a specific Windows x86-64 build of CK2 3.3.5.1. Engine fixes, performance work, and native Linux and macOS support are future work.

## Platform support

| Runtime | Status |
| --- | --- |
| Linux with Proton | The supported PE and achievement script were exercised under Proton 10.0-4. An earlier user test reported success on Steam. |
| Native Windows | The installer can create the same patched PE with standard Python file copying. Native gameplay, Steam launch, and unlock recording still need a Windows test. |
| Native Linux | Requires a Steam Linux depot build, ELF-specific analysis, and verification with its bundled Steam API. The Windows offsets do not apply. |
| Native macOS | Inspect the Mach-O executable and its architecture, check OS compatibility and signing, and test its bundled Steam API. Apple Silicon support depends on the game binary and OS compatibility. The Windows offsets do not apply. |

## Build and run

Requires Python 3.9+ and a matching local Steam installation. The installer checks the SHA-256 hashes of the executable and stock achievement script. It builds an independent copy and fails closed on other builds. Use a new destination outside the Steam installation.

```sh
python3 patch_ck2.py "/absolute/path/to/Crusader Kings II" "/absolute/path/to/CK2-patched"
```

On Linux with Proton, close CK2, save any previous launch options, and set these options in **Steam → Crusader Kings II → Properties → General**:

```text
"/absolute/path/to/launch_ck2.sh" "/absolute/path/to/CK2-patched" %command%
```

On Windows, run the installer with `py -3 patch_ck2.py "C:\path\to\Crusader Kings II" "C:\path\to\CK2-patched"`. For an initial test, open Steam, switch to the copy's directory, and run the copied `CK2game.exe` from there. Confirm CK2 reports Steam active before testing unlocks. Windows launch via the copied executable is a test procedure. Linux's Bash launcher applies only to Proton. To revert, launch the original, restoring prior Steam launch options on Linux.

## Shared local saves

By default CK2 writes into `ck2-patch-profile/save games` inside each copy. For one save directory across multiple patched installations, create an external folder on a volume each OS can access. Build each copy with `--shared-saves` pointing to that same folder using its absolute path on the current OS. The private game profile links only its `save games` folder to the shared directory. Other settings remain local. In the Proton test, a copied save loaded through this link and a new quicksave appeared in the shared directory. Windows directory symlinks require a filesystem that supports them and permission to create them, such as Developer Mode with a supported Windows setup.

With CK2 closed, copy existing local saves into the shared folder:

```sh
python3 import_saves.py "/path/to/old/save games" "/path/to/shared/CK2 saves"
```

The importer copies regular `.ck2` files and stops on name collisions. It leaves the source saves in place. Keep a backup, use one CK2 instance at a time, and test with the same CK2 version, DLC and mods. A common directory cannot make incompatible save formats or mod states load. Mods that redirect the entire CK2 user directory may need a separate setup. Steam Cloud is separate from this local directory. Restore the old launch path to use the old profile again.

## Achievements

Three edits change seven bytes in the supported executable. They let achievement status checks continue with Ironman off and allow the achievement-specific checksum check to pass. The copied `common/achievements.txt` removes 161 scripted Ironman prerequisites. Gameplay triggers, save checks, and CK2's own Steam reporting remain in place. The stock tooltip may still display the Ironman requirement. A mod that replaces the achievement script can supersede these changes.

Verify by playing with a real mod and Ironman disabled, saving and reloading, then meeting the ordinary gameplay condition for an achievement the account has yet to unlock. Check that Steam records it after restarting. A menu indicator is a separate observation. This repository does not distribute CK2 binaries or the Steamworks SDK.

## Companion project

[Unofficial CK2 Common Patch](https://github.com/londonhargrove/unofficial-ck2-common-patch) handles loose-file bugs, gameplay improvements, and content. Its new repository is a separate publication target.

## Credits

The patcher and launcher were written for this project. [JihadJackass’s MAP project](https://github.com/JihadJackass/CK2-Modded-Achievement-Patcher-MAP/tree/83c43104d5cbc950e691e0f3110a91c60898feb7) provided signature references used to identify code in the installed game. The project contains its own static edits and no MAP trampoline implementation. An older, matching CK2 executable and PDB helped identify functions. A [Steam discussion](https://steamcommunity.com/app/203770/discussions/0/3870336629227749731/) provided background.
