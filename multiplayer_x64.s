# CK2 3.3.5.1 Windows PE. Place this code at VA 0x140A9DE7B, immediately
# after the jump over the old Export Game tooltip in load_save.HOOKS.
.set game_mode, get_save_salt + (0x141666c9c - 0x140a9de7b)
.set steam_context, get_save_salt + (0x141667568 - 0x140a9de7b)
.set build_digest, get_save_salt + (0x1400b06de - 0x140a9de7b)
.set free_saved_digest, get_save_salt + (0x1400b074b - 0x140a9de7b)

.intel_syntax noprefix
.global get_save_salt, check_save_digest
get_save_salt:
    # The engine sets game_mode before the host or guest enters the MP lobby.
    cmp dword ptr [rip + game_mode], 0
    je get_steam_salt
    lea rax, [rip + multiplayer_salt]
    ret
get_steam_salt:
    mov rax, [rip + steam_context]
    mov rax, [rax + 0x1c0]
    lea rax, [rax + 0x80]
    ret

check_save_digest:
    # At this point the engine has rewound the save and freed the computed
    # digest. Retry with the local Steam ID for legacy saves.
    cmp byte ptr [rsi + 0x61], 0
    jne finish_check
    lea rax, [rip + multiplayer_salt]
    cmp rdi, rax
    jne finish_check
    call get_steam_salt
    mov rdi, rax
    jmp build_digest
finish_check:
    mov r8, [rbp + 0x47]
    cmp r8, 0x10
    jmp free_saved_digest

# The save code hashes eight bytes in this branch.
multiplayer_salt:
    .ascii "CK2MPv1\0"
