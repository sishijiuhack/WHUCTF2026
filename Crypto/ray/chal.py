from os import urandom
from Crypto.Util.Padding import pad
from AES import AES
import signal
from secret import flag

seed = int.from_bytes(urandom(16))
key = int.from_bytes(urandom(16))
aes = AES(key, seed)
print(f'your flag: {aes.encrypt_ecb(pad(flag, 16)).hex()}')

banner = """
 ____      _ __   __
|  _ \    / \\ \ / /
| |_) |  / _ \\ V / 
|  _ <  / ___ \| |  
|_| \_\/_/   \_\_|  
                    
"""

getattr(signal, 'alarm', lambda _secs: None)(60)

for _ in range(150):
    print(f"make your choice: ")
    match x:= input('[x] > '):
        # change the S-box
        case '1':
            s = int(input('your seed: ') or 0, 16) or None
            k = int(input('your key: ') or 0, 16) or None
            aes.change(s, k)
            print('[+] changed!')
        # encrypt a message
        case '2':
            msg = bytes.fromhex(input('your message: '))
            print(f'Here is your ciphertext (in hex): {aes.encrypt_ecb(pad(msg, 16)).hex()}')
        # reset aes
        case '3':
            aes = AES(key, seed)
            print('reset!')
        case _:
            print('Invalid option!')