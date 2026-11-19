#!/usr/bin/env bash
# Steam launch options: "/path/launch_ck2.sh" "/path/copied game" %command%
set -euo pipefail

if (( $# < 2 )); then
    printf 'Usage: %s PATCHED_GAME_DIRECTORY STEAM_COMMAND...\n' "$0" >&2
    exit 2
fi
game=$(realpath -e -- "$1")
shift
if [[ ! -f $game/CK2game.exe || ! -f $game/userdir.txt || ! -d $game/ck2-patch-profile ]]; then
    printf 'Expected a copy created by patch_ck2.py.\n' >&2
    exit 2
fi
if [[ -z ${SteamAppId:-} || $SteamAppId != 203770 ]]; then
    printf 'Launch this wrapper from the Steam CK2 app.\n' >&2
    exit 2
fi

command=("$@")
matches=0
for i in "${!command[@]}"; do
    if [[ ${command[i]##*/} == CK2game.exe && -f ${command[i]} ]]; then
        command[i]="$game/CK2game.exe"
        (( matches += 1 ))
    fi
done
if (( matches != 1 )); then
    printf 'Expected exactly one CK2game.exe path in the Steam command.\n' >&2
    exit 2
fi
cd -- "$game"
exec "${command[@]}"
