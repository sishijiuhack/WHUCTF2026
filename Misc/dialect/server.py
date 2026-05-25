import socketserver
from typing import Callable, Dict

import dongbei
import shanghai
import sichuan
import yueyu


BANNER = """=== Dialect Sandbox ===
欢迎来到方言沙盒，目标：拿到 flag
输入规则：
1) 按所选方言语法输入代码\n2) 使用单独一行 . 提交执行\n3) 输入 exit 退出
"""

MENU = """请选择方言：
1) 上海话
2) 东北话
3) 四川话
4) 粤语
> """

RUNNERS: Dict[str, Callable] = {
    "1": shanghai.new_runner,
    "2": dongbei.new_runner,
    "3": sichuan.new_runner,
    "4": yueyu.new_runner,
}


class ThreadedHandler(socketserver.StreamRequestHandler):
    def send(self, text: str) -> None:
        self.wfile.write(text.encode("utf-8", errors="replace"))
        self.wfile.flush()

    def recvline(self) -> str:
        data = self.rfile.readline(4096)
        if not data:
            return ""
        return data.decode("utf-8", errors="replace").rstrip("\r\n")

    def choose_runner(self):
        self.send(BANNER)
        while True:
            self.send(MENU)
            c = self.recvline().strip()
            if c in RUNNERS:
                return RUNNERS[c]()
            self.send("无效选择，请重试。\n")

    def handle(self) -> None:
        self.send("\n")
        runner = self.choose_runner()

        buf = []
        while True:
            self.send("dialect> ")
            line = self.recvline()
            if line == "":
                break

            low = line.strip().lower()
            if low in {"exit", "quit", "q"}:
                self.send("bye\n")
                break

            if line.strip() == ".":
                if not buf:
                    self.send("[Info] 空输入，未执行。\n")
                    continue
                _, out = runner.execute(buf)
                self.send("[Output]\n")
                self.send(out if out else "(no output)\n")
                self.send("\n")
                buf.clear()
                continue

            buf.append(line)


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True


def main() -> None:
    host = "0.0.0.0"
    port = 9999
    with ThreadedTCPServer((host, port), ThreadedHandler) as server:
        server.serve_forever()


if __name__ == "__main__":
    main()

