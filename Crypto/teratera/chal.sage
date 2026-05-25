from Crypto.Util.number import *
from random import *
from hashlib import md5
from Crypto.Cipher import AES
from secret import flag, e

p = 2313495809
R.<x> = PolynomialRing(Zmod(p), 'x')
N = 256
f = x^N - 1
length = N // 4
a = R([randint(0, p-1) for _ in range(N)])
s = R([randint(0, p-1) for _ in range(length)])
E = R([choice(e) for i in range(N)])

b = (a * s + E).mod(f)

key = md5(str(s).encode()).hexdigest()
cipher = AES.new(bytes.fromhex(key), mode=AES.MODE_CTR, nonce=b'teratera')
ct = cipher.encrypt(flag).hex()

with open('output.txt', 'w') as f:
    f.write(f"a = {a}\n")
    f.write(f"b = {b}\n")
    f.write(f"e = {e}\n")
    f.write(f"ct = {ct}\n")