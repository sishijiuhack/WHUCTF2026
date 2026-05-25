import base64
import os
import random
import socketserver

from myhash import whu_md5_hex
from secret import secret_key, flag

secret_key = bytes.fromhex(secret_key) 
gift_message = b"Hash_is_a_gift_from_heaven"
pad_byte = random.randrange(0x100)


def gift_token():
    sig = whu_md5_hex(secret_key + gift_message, pad_lead=pad_byte)
    return base64.b64encode(gift_message).decode(), sig


def submit(data_b64: str, sig: str):
    sig = sig.strip().lower()
    if len(sig) != 32:
        return {"ok": False, "error": "Invalid signature format"}
    
    try:
        msg = base64.b64decode(data_b64, validate=True)
    except Exception:
        return {"ok": False, "error": "invalid base64"}

    expected = whu_md5_hex(secret_key + msg, pad_lead=pad_byte)
    
    if expected != sig:
        return {"ok": False, "error": "signature mismatch"}

    if b"GetFlag" in msg:
        return {"ok": True, "flag": flag}
    return {"ok": True, "msg": "You win! But why not get the flag?"}


    
class ChallengeHandler(socketserver.StreamRequestHandler):
    def _send_line(self, text: str = ""):
        self.wfile.write((text + "\n").encode())
        self.wfile.flush()

    def _read_prompt(self, prompt: str):
        self.wfile.write(prompt.encode())
        self.wfile.flush()
        data = self.rfile.readline()
        if not data:
            return None
        return data.decode(errors="replace").strip()

    def handle(self):
        while True:
            self._send_line("1) Get token")
            self._send_line("2) Submit data+sig")
            self._send_line("3) Exit")
            choice = self._read_prompt("Choice> ")
            if choice is None:
                return

            if choice == "1":
                data, sig = gift_token()
                self._send_line(f"TOKEN data={data} sig={sig}")
            
            elif choice == "2":
                data_b64 = self._read_prompt("DATA_B64> ")
                if data_b64 is None:
                    return
                sig = self._read_prompt("SIG> ")
                if sig is None:
                    return
                result = submit(data_b64, sig)
                if result.get("ok") and "flag" in result:
                    self._send_line(f"flag={result['flag']}")
                elif result.get("ok"):
                    self._send_line(f"msg={result['msg']}")
                else:
                    self._send_line(f"error={result['error']}")
                    
            elif choice == "3":
                self._send_line("bye")
                return
            else:
                self._send_line("invalid choice")
            self._send_line()


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True


def serve():
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "9999"))
    with ThreadedTCPServer((host, port), ChallengeHandler) as server:
        print(f"[+] Listening on {host}:{port}")
        server.serve_forever()


if __name__ == "__main__":
    serve()
