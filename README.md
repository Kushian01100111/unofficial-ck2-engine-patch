# CK2 Proton achievement patch

Builds a separate copy of Crusader Kings II 3.3.5.1 for Steam and Proton. The patch lets CK2's achievement checks proceed with Ironman disabled and with checksum-changing mods. CK2 still evaluates its gameplay triggers and uses its own Steam reporting code. Support is limited to the Windows x86-64 executable and stock achievement definitions identified by the hashes in `patch_ck2.py`.

A modded non-Ironman campaign was saved, reloaded after restarting Proton, and saved again in offline testing. A user subsequently reported that the patch worked on their Steam setup. Mods that replace `common/achievements.txt` may require their own compatible definitions. CK2's stock tooltip may still list the Ironman requirement.

## Setup

Requires Python 3.9+, GNU coreutils and a Steam installation of CK2 configured to use Proton. Close CK2 before changing its Steam launch options.

```bash
python3 patch_ck2.py "/absolute/path/to/Crusader Kings II" "/absolute/path/to/CK2-patched"
```

Use a destination that does not exist and is outside the Steam installation. In Steam, open **Crusader Kings II → Properties → General** and record any existing launch options. Set the following, substituting your actual absolute paths.

```text
"/absolute/path/to/launch_ck2.sh" "/absolute/path/to/CK2-patched" %command%
```

The copied game keeps its local saves and settings in `ck2-patch-profile`. Start a fresh local game for the first test. For local mods, put the mod and its descriptor under the private profile's `mod` directory. To revert, close CK2 and restore the previous launch options. Keep the copy if you want to retain its saves.

## Implementation and credits

The patcher and launcher were written for this project. The patcher changes seven executable bytes across three instruction sites and replaces 161 Ironman predicates in the user's local achievement definitions. This repository contains source and documentation only.

[JihadJackass's CK2 Modded Achievement Patcher](https://github.com/JihadJackass/CK2-Modded-Achievement-Patcher-MAP/tree/83c43104d5cbc950e691e0f3110a91c60898feb7) was a reverse-engineering reference. Its published signatures helped identify nearby code in the installed executable, including the achievement checksum flag. This project uses its own static edits and does not include MAP's implementation or trampoline payloads. A matching older CK2 executable and PDB also helped identify functions. A [Steam community discussion](https://steamcommunity.com/app/203770/discussions/0/3870336629227749731/) was consulted for background.
