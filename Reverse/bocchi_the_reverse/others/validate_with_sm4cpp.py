import subprocess
import sys


def run_cmd(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, p.stdout.strip(), p.stderr.strip()


def main():
    rc, out, err = run_cmd(["java", "Sm4VmRunner", "--hex"])
    if rc != 0:
        print("[FAIL] Java VM 运行失败")
        print(err)
        return 2
    vm_hex = out.strip().lower()

    rc, cpp_out, cpp_err = run_cmd([".\\sm4_ref.exe"])
    if rc != 0:
        print("[FAIL] sm4_ref.exe 运行失败")
        print(cpp_err)
        return 2
    cpp_hex = cpp_out.strip().lower()

    print("cpp.hex =", cpp_hex)
    print("vm.hex  =", vm_hex)

    if vm_hex == cpp_hex:
        print("[PASS] Java VM 与 sm4.cpp 结果一致")
        return 0

    print("[FAIL] Java VM 与 sm4.cpp 结果不一致")
    return 1


if __name__ == "__main__":
    sys.exit(main())
