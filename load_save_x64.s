# CK2 3.3.5.1 Windows PE. The first instruction is placed at VA 0x140F99202.
# Stock addresses are expressed relative to that point for RIP-relative operands.
.set picker_mode, open_load + (0x14185bd74 - 0x140f99202)
.set load_pending, open_load + (0x14185bd75 - 0x140f99202)
.set chosen_length, open_load + (0x14185bd78 - 0x140f99202)
.set chosen_name, open_load + (0x14185bd80 - 0x140f99202)
.set start_save, open_load + (0x141771b68 - 0x140f99202)
.set stock_start_save, open_load + (0x140711c20 - 0x140f99202)
.set frontend_return, open_load + (0x14070fe4e - 0x140f99202)
.set open_picker_continue, open_load + (0x14067b5a5 - 0x140f99202)
.set close_picker_continue, open_load + (0x14067b398 - 0x140f99202)
.set delete_save_continue, open_load + (0x140680ceb - 0x140f99202)
.set cloud_tab_continue, open_load + (0x14066e3b6 - 0x140f99202)
.set local_tab_continue, open_load + (0x14066e386 - 0x140f99202)
.set caption_continue, open_load + (0x14067d304 - 0x140f99202)
.set load_caption, open_load + (0x1410892e0 - 0x140f99202)
.set localize, open_load + (0x1406996a0 - 0x140f99202)
.set set_button_caption, open_load + (0x140cd7200 - 0x140f99202)
.set free_string, open_load + (0x1400af430 - 0x140f99202)
.set assign_string, open_load + (0x1400b1240 - 0x140f99202)
.set quit_to_menu, open_load + (0x14064ba80 - 0x140f99202)
.set stock_cleanup, open_load + (0x140681f13 - 0x140f99202)
.set stock_submit_continue, open_load + (0x14068194c - 0x140f99202)

.intel_syntax noprefix
.global open_load, open_save, close_picker, capture_save, submit_picker, resume_save
.global delete_save, cloud_tab, local_tab, update_caption
# The former Export button reuses the stock local Save Game panel.
open_load:
    mov byte ptr [rip + picker_mode], 1
    mov byte ptr [rcx + 0x41d8], 0
    jmp open_picker
open_save:
    mov byte ptr [rip + picker_mode], 0
open_picker:
    and qword ptr [rip + chosen_length], 0
    mov [rsp + 8], rcx
    jmp open_picker_continue

close_picker:
    mov byte ptr [rip + picker_mode], 0
    mov rax, rsp
    push rdi
    sub rsp, 0x70
    jmp close_picker_continue

# Record the stock row name before the save UI copies it into the editable field.
# Keep the original SetString arguments and only accept a local filename.
capture_save:
    cmp byte ptr [rip + picker_mode], 1
    jne capture_done
    and qword ptr [rip + chosen_length], 0
    test r8, r8
    je capture_done
    cmp r8, 235
    ja capture_done
    lea r10, [rip + chosen_name]
    xor eax, eax
copy_name:
    mov r9b, [rdx + rax]
    cmp r9b, '/'
    je capture_done
    cmp r9b, 92
    je capture_done
    mov [r10 + rax], r9b
    inc eax
    cmp rax, r8
    jb copy_name
    cmp eax, 4
    jb append_extension
    cmp dword ptr [r10 + rax - 4], 0x326b632e
    je name_ready
append_extension:
    mov dword ptr [r10 + rax], 0x326b632e
    add eax, 4
name_ready:
    mov byte ptr [r10 + rax], 0
    mov [rip + chosen_length], rax
capture_done:
    jmp assign_string

# Stock Save Game continues to its original write path. In load mode only a
# selected row can queue the engine transition.
submit_picker:
    cmp byte ptr [rip + picker_mode], 1
    jne stock_submit
    cmp qword ptr [rip + chosen_length], 0
    je submit_done
    mov byte ptr [rip + picker_mode], 0
    mov byte ptr [rip + load_pending], 1
    mov rcx, r13
    call quit_to_menu
submit_done:
    jmp stock_cleanup
stock_submit:
    cmp qword ptr [rbp - 0x50], 0
    je submit_done
    jmp stock_submit_continue

# At the end of frontend initialization, consume the same one-shot name as
# the startup loader. This avoids opening the main menu Load Game browser.
resume_save:
    cmp byte ptr [rip + load_pending], 1
    jne resume_done
    mov byte ptr [rip + load_pending], 0
    mov r8, [rip + chosen_length]
    and qword ptr [rip + chosen_length], 0
    lea rcx, [rip + start_save]
    lea rdx, [rip + chosen_name]
    call assign_string
    mov rcx, r14
    call stock_start_save
resume_done:
    lea r11, [rsp + 0x250]
    jmp frontend_return

delete_save:
    cmp byte ptr [rip + picker_mode], 1
    je action_blocked
    mov rax, rsp
    push rdi
    sub rsp, 0x80
    jmp delete_save_continue

cloud_tab:
    cmp byte ptr [rip + picker_mode], 1
    je action_blocked
    push rbx
    sub rsp, 0x20
    jmp cloud_tab_continue

local_tab:
    cmp byte ptr [rip + picker_mode], 1
    je action_blocked
    push rbx
    sub rsp, 0x20
    jmp local_tab_continue

action_blocked:
    ret

# Keep the existing standard button and font, with the stock localized caption.
update_caption:
    sub rsp, 0x50
    mov qword ptr [rsp + 0x20], 0x65766173
    mov qword ptr [rsp + 0x30], 4
    mov qword ptr [rsp + 0x38], 15
    lea rdx, [rsp + 0x20]
    mov rcx, r14
    mov rax, [rcx]
    call qword ptr [rax + 0x78]
    test rax, rax
    je caption_done
    mov [rsp + 0x40], rax
    lea rdx, [rip + save_caption]
    cmp byte ptr [rip + picker_mode], 1
    jne caption_key
    lea rdx, [rip + load_caption]
caption_key:
    lea rcx, [rsp + 0x20]
    call localize
    mov rdx, rax
    mov rcx, [rsp + 0x40]
    xor r8d, r8d
    call set_button_caption
    lea rcx, [rsp + 0x20]
    call free_string
caption_done:
    add rsp, 0x50
    mov rcx, [r12 + 0x6618]
    jmp caption_continue

save_caption:
    .asciz "MENU_BAR_SAVE"
