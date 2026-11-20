# Unofficial CK2 Engine Patch

An unofficial patch for **Crusader Kings II (CK2)** that adds new features and improves the game without replacing the original game engine.

This project was made with help from AI.

**Important:** You must own a copy of Crusader Kings II to use this patch. This project does not include the original game files or the Steamworks SDK.

## What Does This Patch Do?

This patch adds several useful features:

- **Load saves while playing:** Load another save without returning to the main menu.
- **Achievements with mods:** Earn Steam achievements while using mods or playing without Ironman Mode.

More features may be added in the future.

---

## What You Need

Before installing, make sure you have:

- **Python 3.9 or newer** installed on your computer.
- **Crusader Kings II** installed.

## How to Install

### Step 1: Make a Patched Copy of CK2

The patcher creates a new copy of your CK2 installation with the improvements added.

**Your original game files will not be changed.**

Open a terminal (Linux/macOS) or Command Prompt (Windows) and run the command for your system.

**Linux / macOS:**

```bash
python3 patch_ck2.py "/path/to/Crusader Kings II" "/path/to/CK2-patched"
```

**Windows:**

```powershell
py -3 patch_ck2.py "C:\path\to\Crusader Kings II" "C:\path\to\CK2-patched"
```

Replace the example paths with the real locations of your game folder and where you want the patched copy to go.

### Step 2: Set Up Steam

To make Steam launch your patched version:

1. Open **Steam**.
2. Find **Crusader Kings II** in your library.
3. Right-click the game and select **Properties**.
4. Open the **General** section.
5. Find **Launch Options**.
6. Enter the following command, replacing the example paths with your own:

```bash
"/absolute/path/to/launch_ck2.sh" "/absolute/path/to/CK2-patched" %command%
```

**Optional: Load Straight Into a Save**

If you want CK2 to open a particular save automatically, use:

```bash
"/absolute/path/to/launch_ck2.sh" "/absolute/path/to/CK2-patched" %command% -skiplauncher "-start_save=My Save.ck2"
```

Replace `My Save.ck2` with the name of your save file.

If you leave out the extra options, CK2 will open its launcher normally so you can choose your mods and DLC.

### Step 3: Take Jerusalem!

You're ready to play CK2 with the new features!

---

## Features Explained

### 1. Load Saves Without Leaving Your Game

Normally, CK2 makes you return to the main menu to load another save.

**This patch lets you load a save directly from the pause menu.**

How to use it:

1. Start or load a CK2 campaign.
2. Open the pause menu using ESC.
3. Click **Load Save**, just below **Save Game**.
4. Choose the save you want.
5. Click **Load** to switch to that save, or **Back** to continue playing.

**Be careful:** Loading another save will remove any progress you haven't saved.

The patch uses CK2's original save-loading system, so the game still handles loading and checking saves normally.

It also keeps your music playing instead of restarting it when you load another save.

**What has been tested?**

This feature has been tested with:

- Offline single-player games.
- Proton 10.0-4 on Linux.
- Compressed and uncompressed saves.
- Switching between different rulers.
- Saves stored inside folders up to two levels deep.

**What hasn't been tested yet?**

- Steam Cloud saves.
- Multiplayer.
- Ironman Mode.
- Running the patch directly on Windows without Proton or Wine.

### 2. Earn Achievements With Mods

Normally, CK2 has restrictions on when you can earn Steam achievements.

This patch removes the Ironman requirement and changes the achievement checks so you can earn achievements while using mods.

**What changes?**

- Ironman Mode is no longer required for achievements.
- The achievement checksum restriction is bypassed.
- 161 Ironman requirements are removed from the copied achievement files.
- Normal achievement goals still need to be completed.

For example, if an achievement requires you to conquer a certain kingdom, you still need to conquer it.

**Important:** Some mods replace CK2's achievement files. These mods may interfere with the patch.

**How to test achievements:**

1. Start a game with a mod enabled.
2. Turn Ironman Mode off.
3. Save and reload your game.
4. Complete an achievement you haven't earned before.
5. Restart the game and check Steam to see whether it recorded the achievement.

An achievement appearing as available in the game doesn't always mean Steam has awarded it.

### 3. Share Save Files Between Different CK2 Installations

Normally, each patched copy of CK2 keeps its saves in its own folder:

`ck2-patch-profile/save games`

This patch also lets multiple patched copies use the same save folder.

This can be useful if you play CK2 on both Windows and Linux, or have several patched installations.

**Step 1: Create a Shared Save Folder**

Make a folder somewhere both installations can access, such as a shared drive.

**Step 2: Tell the Patcher Where It Is**

When creating your patched copy, add `--shared-saves` to the command:

```bash
python3 patch_ck2.py "/path/to/Crusader Kings II" "/path/to/CK2-patched" --shared-saves "/path/to/shared/CK2 saves"
```

Do this for each patched installation that you want to share saves.

**Step 3: Move Your Existing Saves**

If you already have CK2 saves, you can copy them into the shared folder using:

```bash
python3 import_saves.py "/path/to/old/save games" "/path/to/shared/CK2 saves"
```

This tool copies your `.ck2` save files without deleting the originals.

If two files have the same name, the tool stops rather than overwriting one.

**Things to remember:**

- Only save files are shared. Your other game settings remain separate.
- Back up your saves before making changes.
- Don't run two copies of CK2 using the same save folder at once.
- Keep your CK2 versions, DLC, and mods the same to avoid save compatibility problems.
- Steam Cloud saves are separate and are not automatically shared.
- On Windows, shared folders using symbolic links may require Developer Mode or special permissions.
- Mods that change the location of CK2's user files may require additional setup.

---

## Technical Details (For Advanced Users)

This section explains how the patch works behind the scenes. You can skip it if you just want to play.

**Save Loading**

Instead of returning to the main menu, the patch sends your chosen save file to CK2's built-in startup save loader.

It then displays a loading screen while CK2 prepares the save.

This allows the game to load another campaign without using the normal main-menu process.

**Achievement Changes**

The patch changes 7 bytes across 3 locations in the supported CK2 executable.

It also removes 161 Ironman requirements from the copied `common/achievements.txt` file and updates the Game Rules achievement checks.

The normal achievement conditions and Steam reporting system are left in place.

**Compatibility**

The save-loading feature has been tested using Proton 10.0-4.

An additional WineD3D test showed some terrain graphics problems, but these also appeared during normal gameplay, not just after loading saves.

More testing is needed for other systems and game modes.

---

## Companion Project

**Unofficial CK2 Common Patch**

This is a separate project focused on fixing bugs and improving gameplay through CK2's normal game files.

While the **Engine Patch** changes how the game itself works, the **Common Patch** focuses on things like:

- Bug fixes.
- Gameplay improvements.
- Changes to game content.

The two projects have different purposes.

---

## Disclaimer

This is an unofficial community project and is not made, supported, or approved by Paradox Interactive.

You must have your own legitimate copy of Crusader Kings II.

The project does not distribute CK2 executables or the Steamworks SDK.
