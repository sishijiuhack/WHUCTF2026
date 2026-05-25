from Crypto.Util.number import *
from secret import flag

file = open("output.txt", "w")

m = bytes_to_long(flag)
p = getPrime(512)
q = getPrime(512)

N = p * q
file.write(f"{N = }\n")

e = getRandomRange(1024, N)

def lcg(x):
    return (2 * x + 2026) % N

for i in range(1,10):
    e1 = e  
    e2 = e
    for j in range(i):
        e1 = lcg(e1)
        e2 = lcg(lcg(e2))
    c1 = pow(m, e1, N)
    c2 = pow(m, e2, N)
    file.write(f"{c1 + c2}\n")
    
file.close()

