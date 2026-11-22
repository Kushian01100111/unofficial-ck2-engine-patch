# CK2 3.3.5.1 Windows PE, VA 0x140C31E19. The stock blob writer's prologue,
# field tag and epilogue still run. R15 is the writer and R14 is the blob.
.set open_group, write_blob + (0x140c317f0 - 0x140c31e19)
.set encode_base64, write_blob + (0x140d6ca30 - 0x140c31e19)
.set write_string, write_blob + (0x140c31990 - 0x140c31e19)
.set close_group, write_blob + (0x140c3231f - 0x140c31e19)
.set field_size, 510
.set raw_window, 384
.set raw_stride, 381

.intel_syntax noprefix
.global write_blob
write_blob:
    mov dl, 1
    mov rcx, r15
    call open_group

    mov rsi, [r14 + 8]
    mov edi, [r14 + 0x14]
    lea r13, [rbp - 0x74]
    xor r12d, r12d
    test edi, edi
    jle done

write_field:
    # Base64 groups consume three bytes and produce four characters. The
    # stock 510-character fields alternate between group offsets 0 and 2.
    # Encode at most 384 input bytes and overlap one group on alternate fields.
    mov r8d, raw_window
    cmp edi, r8d
    cmovb r8d, edi
    mov rcx, r13
    sub rcx, r12
    mov rdx, rsi
    call encode_base64
    sub eax, r12d
    cmp eax, field_size
    mov ebx, field_size
    cmovb ebx, eax
    mov byte ptr [r13 + rbx], 0
    # Set the token after encoding because the two skipped bytes overlap it.
    mov dword ptr [rbp - 0x78], 0xf
    lea rdx, [rbp - 0x78]
    mov rcx, r15
    call write_string

    # Advance 381 bytes for offset 0, or 384 for offset 2.
    mov ebx, raw_stride
    mov eax, raw_window
    test r12d, r12d
    cmovne ebx, eax
    add rsi, rbx
    xor r12d, 2
    sub edi, ebx
    jg write_field
done:
    jmp close_group
