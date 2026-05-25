from Crypto.Util.number import *
from random import randint
from math import gcd, lcm
from hashlib import sha256
from ast import literal_eval

from secret import flag

banner = """
[8]======================================================[8]
 |                                                        |
 |    A AAAAAA     IIIIII     ZZZZZZZZ     OOOOOOO        |
 |   A  AA  AA       II             ZZ    OO     OO       |
 |  AA      AA       II           ZZ      OO     OO       |
 |  AAAAAAAAAA       II         ZZ        OO     OO       |
 |  AA      AA     IIIIII     ZZZZZZZZ     OOOOOOO        |
 |                                                        |
[8]==================== L O O P =========================[8]
"""


class AIZO:
    def __init__(self):
        self.rp = getPrime(255)
        self.rq = getPrime(255)
        while not isPrime(2 * self.rp + 1):
            self.rp = getPrime(255)
        while not isPrime(2 * self.rq + 1):
            self.rq = getPrime(255)
        self.p = 2 * self.rp + 1
        self.q = 2 * self.rq + 1
        self.N = self.p * self.q
        self.phiN = (self.p - 1) * (self.q - 1)
        self.lambdaN = lcm(self.p - 1, self.q - 1)
        self.bound = 2**250
        while True:
            self.g1 = randint(2, self.N - 1)
            self.g2 = randint(2, self.N - 1)
            if gcd(self.g1, self.N) == 1 and gcd(self.g2, self.N) == 1 and self.g1 != 1 and self.g2 != 1:
                break

    def keygen(self):
        self.s = randint(1, self.bound - 1)
        self.t = randint(1, self.bound - 1)
        self.pk = (pow(self.g1, self.s, self.N) * pow(self.g2, self.t, self.N)) % self.N
        return self.pk, self.g1, self.g2, self.N, self.p, self.q

    def sign(self, m):
        h = int(sha256(m).hexdigest(), 16)
        while True:
            e1 = randint(1, self.bound - 1)
            e2 = randint(1, self.bound - 1)
            if gcd(e1, self.lambdaN) == 1 and gcd(e2, self.N) == 1:
                break
        S1 = (pow(self.g1, e1, self.N) * pow(self.g2, e2, self.N)) % self.N
        S2 = (h - self.s * S1) * inverse(e1, self.lambdaN) % self.lambdaN
        S3 = (h - self.t * S1 - e2 * S2) % self.lambdaN
        return S1, S2, S3

    def verify(self, m, sigma):
        e1, e2, S2, S3 = sigma
        h = int(sha256(m).hexdigest(), 16)

        if not (1 <= e1 < self.lambdaN and 1 <= e2 < self.N):
            return False
        if not (0 <= S2 < self.lambdaN and 0 <= S3 < self.lambdaN):
            return False
        if gcd(e1, self.lambdaN) != 1 or gcd(e2, self.N) != 1:
            return False
        S1 = (pow(self.g1, e1, self.N) * pow(self.g2, e2, self.N)) % self.N
        Y1 = pow(self.pk, S1, self.N) * pow(S1, S2, self.N) * pow(self.g2, S3, self.N) % self.N
        Y2 = pow((self.g1 * self.g2), h, self.N)
        return Y1 == Y2


print(banner)
print(" welcome to The Culling Game! ")

Migration = AIZO()
pk, g1, g2, N, p, q = Migration.keygen()
print("pk: ", pk)
print("g1: ", g1)
print("g2: ", g2)
print("N: ", N)
print("p: ", p)
print("q: ", q)


loop = 4
for i in range(loop):
    print(f"Round {i+1}:")
    try:
        option = input("make your choice : ")
        if option == "LUV ME":
            m = input("your message: ").encode()
            if m != b"kenjaku":
                sigma = Migration.sign(m)
                print("your sign: ", sigma)
        if option == "HATE ME":
            print("only kenjaku can stop the migration")
            print("submit (e1, e2, S2, S3)")
            sigma = literal_eval(input("your sign: "))
            if Migration.verify(b"kenjaku", sigma):
                print("just KILL ME ", flag)
                break
            else:
                print("So then, let us meet again.")
    except Exception as e:
        print("Error: ", e)
        continue
