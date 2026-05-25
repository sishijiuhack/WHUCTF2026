import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.Base64;

public class Sm4VmRunner {

    private static final int CODE_BASE = 0x1000;
    private static final int INSTR_SIZE = 8;
    private static final int SBOX_SIZE = 256;
    private static final int SBOX_BASE = 0x0500;

    private static final int TEXT_BASE = 0x0000;
    private static final int OUTPUT_LEN = 64;
    private static final String PLAINTEXT = "\u0000".repeat(OUTPUT_LEN);
    private static final String KEY_TEXT = "bocchi_the_rock!";

    // Prebuilt single blob: [SBOX(256 bytes)] + [program bytes]
    private static final byte[] SM4_PROGRAM = Base64.getDecoder().decode(
            "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");

    enum Opcode {
        NOP(0x00), HALT(0x01), LDI(0x02), MOV(0x03), LDWBE(0x04), STWBE(0x05),
        XOR(0x06), XORI(0x07), ANDI(0x08), SHLI(0x09), SHR(0x0A), ROLI(0x0B),
        ADDI(0x0C), CMP(0x0D), JMP(0x0E), JCC(0x0F), PUSH(0x10), POP(0x11), TBL8(0x12);

        final int code;

        Opcode(int code) {
            this.code = code;
        }

        static Opcode fromCode(int code) {
            for (Opcode value : values()) {
                if (value.code == code) {
                    return value;
                }
            }
            throw new IllegalArgumentException("Illegal opcode: 0x" + Integer.toHexString(code));
        }
    }

    static final class Cond {
        static final int EQ = 0;
        static final int NE = 1;
        static final int LT = 2;
        static final int LE = 3;
        static final int GT = 4;
        static final int GE = 5;
    }

    static final class VmState {
        int[] regs = new int[16];
        int[] stack = new int[1024];
        int sp;
        int ip;
        int cmp;
        boolean halted;
        byte[] memory;

        VmState(int memorySize) {
            memory = new byte[memorySize];
        }
    }

    static final class VirtualMachine {
        private final VmState s;
        private final int codeBase;
        private final int codeSize;

        VirtualMachine(VmState state, int codeBase, int codeSize) {
            this.s = state;
            this.codeBase = codeBase;
            this.codeSize = codeSize;
        }

        void run() {
            while (!s.halted) {
                if (s.ip < codeBase || s.ip + INSTR_SIZE > codeBase + codeSize) {
                    throw new IllegalStateException("IP out of code range: " + s.ip);
                }
                step();
            }
        }

        private void step() {
            int ip = s.ip;
            int opCode = s.memory[ip] & 0xFF;
            int a = s.memory[ip + 1] & 0xFF;
            int b = s.memory[ip + 2] & 0xFF;
            int c = s.memory[ip + 3] & 0xFF;
            int imm = (s.memory[ip + 4] & 0xFF)
                    | ((s.memory[ip + 5] & 0xFF) << 8)
                    | ((s.memory[ip + 6] & 0xFF) << 16)
                    | ((s.memory[ip + 7] & 0xFF) << 24);

            Opcode op = Opcode.fromCode(opCode);
            switch (op) {
                case NOP -> s.ip += INSTR_SIZE;
                case HALT -> s.halted = true;
                case LDI -> {
                    s.regs[a] = imm;
                    s.ip += INSTR_SIZE;
                }
                case MOV -> {
                    s.regs[a] = s.regs[b];
                    s.ip += INSTR_SIZE;
                }
                case LDWBE -> {
                    int addr = s.regs[b] + imm;
                    s.regs[a] = readU32BE(addr);
                    s.ip += INSTR_SIZE;
                }
                case STWBE -> {
                    int addr = s.regs[b] + imm;
                    writeU32BE(addr, s.regs[a]);
                    s.ip += INSTR_SIZE;
                }
                case XOR -> {
                    s.regs[a] = s.regs[b] ^ s.regs[c];
                    s.ip += INSTR_SIZE;
                }
                case XORI -> {
                    s.regs[a] = s.regs[b] ^ imm;
                    s.ip += INSTR_SIZE;
                }
                case ANDI -> {
                    s.regs[a] = s.regs[b] & imm;
                    s.ip += INSTR_SIZE;
                }
                case SHLI -> {
                    int sh = imm & 31;
                    s.regs[a] = s.regs[b] << sh;
                    s.ip += INSTR_SIZE;
                }
                case SHR -> {
                    int sh = imm & 31;
                    s.regs[a] = s.regs[b] >>> sh;
                    s.ip += INSTR_SIZE;
                }
                case ROLI -> {
                    int sh = imm & 31;
                    s.regs[a] = Integer.rotateLeft(s.regs[b], sh);
                    s.ip += INSTR_SIZE;
                }
                case ADDI -> {
                    s.regs[a] = s.regs[b] + imm;
                    s.ip += INSTR_SIZE;
                }
                case CMP -> {
                    s.cmp = Integer.compare(s.regs[a], s.regs[b]);
                    s.ip += INSTR_SIZE;
                }
                case JMP -> s.ip = s.ip + INSTR_SIZE + imm * INSTR_SIZE;
                case JCC -> {
                    boolean take = switch (a) {
                        case Cond.EQ -> s.cmp == 0;
                        case Cond.NE -> s.cmp != 0;
                        case Cond.LT -> s.cmp < 0;
                        case Cond.LE -> s.cmp <= 0;
                        case Cond.GT -> s.cmp > 0;
                        case Cond.GE -> s.cmp >= 0;
                        default -> throw new IllegalStateException("Bad cond: " + a);
                    };
                    s.ip = take ? (s.ip + INSTR_SIZE + imm * INSTR_SIZE) : (s.ip + INSTR_SIZE);
                }
                case PUSH -> {
                    if (s.sp >= s.stack.length) {
                        throw new IllegalStateException("Stack overflow");
                    }
                    s.stack[s.sp++] = s.regs[a];
                    s.ip += INSTR_SIZE;
                }
                case POP -> {
                    if (s.sp <= 0) {
                        throw new IllegalStateException("Stack underflow");
                    }
                    s.regs[a] = s.stack[--s.sp];
                    s.ip += INSTR_SIZE;
                }
                case TBL8 -> {
                    int base = s.regs[c];
                    int idx = s.regs[b] & 0xFF;
                    int addr = base + idx;
                    checkRange(addr, 1);
                    s.regs[a] = s.memory[addr] & 0xFF;
                    s.ip += INSTR_SIZE;
                }
                default -> throw new IllegalStateException("Unhandled opcode");
            }
        }

        private int readU32BE(int addr) {
            checkRange(addr, 4);
            return ((s.memory[addr] & 0xFF) << 24)
                    | ((s.memory[addr + 1] & 0xFF) << 16)
                    | ((s.memory[addr + 2] & 0xFF) << 8)
                    | (s.memory[addr + 3] & 0xFF);
        }

        private void writeU32BE(int addr, int value) {
            checkRange(addr, 4);
            s.memory[addr] = (byte) ((value >>> 24) & 0xFF);
            s.memory[addr + 1] = (byte) ((value >>> 16) & 0xFF);
            s.memory[addr + 2] = (byte) ((value >>> 8) & 0xFF);
            s.memory[addr + 3] = (byte) (value & 0xFF);
        }

        private void checkRange(int addr, int len) {
            if (addr < 0 || addr + len > s.memory.length) {
                throw new IllegalStateException("Memory out of range addr=" + addr + " len=" + len);
            }
        }
    }

    private static byte[] runEncryptionInVm() {
        byte[] plaintextBytes = PLAINTEXT.getBytes(StandardCharsets.US_ASCII);
        byte[] keyBytes = KEY_TEXT.getBytes(StandardCharsets.US_ASCII);
        byte[] sboxBytes = Arrays.copyOfRange(SM4_PROGRAM, 0, SBOX_SIZE);
        byte[] programTemplate = Arrays.copyOfRange(SM4_PROGRAM, SBOX_SIZE, SM4_PROGRAM.length);
        byte[] program = injectInputsIntoProgram(programTemplate, plaintextBytes, keyBytes);

        VmState state = new VmState(0x8000);
        state.ip = CODE_BASE;

        // load SBOX bytes into VM memory; TBL8 will read by memory address
        System.arraycopy(sboxBytes, 0, state.memory, SBOX_BASE, SBOX_SIZE);

        // put bytecode into memory and execute by IP fetch
        System.arraycopy(program, 0, state.memory, CODE_BASE, program.length);

        VirtualMachine vm = new VirtualMachine(state, CODE_BASE, program.length);
        vm.run();

        byte[] out = new byte[OUTPUT_LEN];
        System.arraycopy(state.memory, TEXT_BASE, out, 0, OUTPUT_LEN);
        return out;
    }

    private static byte[] injectInputsIntoProgram(byte[] programTemplate, byte[] plaintext, byte[] key) {
        if (plaintext.length != OUTPUT_LEN) {
            throw new IllegalArgumentException("plaintext must be exactly " + OUTPUT_LEN + " bytes");
        }
        if (key.length != 16) {
            throw new IllegalArgumentException("key must be exactly 16 bytes");
        }

        int[] textWords = toWordsBe(plaintext);
        int[] keyWords = toWordsBe(key);

        byte[] patched = Arrays.copyOf(programTemplate, programTemplate.length);
        int textIdx = 0;
        int keyIdx = 0;

        // Patch pattern:
        //   LDI R0, imm32
        //   STWBE R0, [R10 + off]   -> plaintext init
        //   STWBE R0, [R11 + off]   -> key init
        for (int pc = 0; pc + 2 * INSTR_SIZE <= patched.length; pc += INSTR_SIZE) {
            int op = patched[pc] & 0xFF;
            int a = patched[pc + 1] & 0xFF;
            int b = patched[pc + 2] & 0xFF;
            int c = patched[pc + 3] & 0xFF;
            if (op != Opcode.LDI.code || a != 0 || b != 0 || c != 0) {
                continue;
            }

            int nextPc = pc + INSTR_SIZE;
            int nextOp = patched[nextPc] & 0xFF;
            int nextA = patched[nextPc + 1] & 0xFF;
            int nextB = patched[nextPc + 2] & 0xFF;
            if (nextOp != Opcode.STWBE.code || nextA != 0) {
                continue;
            }

            if (nextB == 10 && textIdx < textWords.length) {
                writeImmLe(patched, pc + 4, textWords[textIdx++]);
            } else if (nextB == 11 && keyIdx < keyWords.length) {
                writeImmLe(patched, pc + 4, keyWords[keyIdx++]);
            }
        }

        if (textIdx != textWords.length || keyIdx != keyWords.length) {
            throw new IllegalStateException("Failed to patch all text/key words into program template");
        }
        return patched;
    }

    private static int[] toWordsBe(byte[] data) {
        if ((data.length & 3) != 0) {
            throw new IllegalArgumentException("length must be multiple of 4");
        }
        int[] out = new int[data.length / 4];
        for (int i = 0; i < out.length; i++) {
            int p = i * 4;
            out[i] = ((data[p] & 0xFF) << 24)
                    | ((data[p + 1] & 0xFF) << 16)
                    | ((data[p + 2] & 0xFF) << 8)
                    | (data[p + 3] & 0xFF);
        }
        return out;
    }

    private static void writeImmLe(byte[] code, int immOffset, int value) {
        code[immOffset] = (byte) (value & 0xFF);
        code[immOffset + 1] = (byte) ((value >>> 8) & 0xFF);
        code[immOffset + 2] = (byte) ((value >>> 16) & 0xFF);
        code[immOffset + 3] = (byte) ((value >>> 24) & 0xFF);
    }

    private static String bytesToHex(byte[] data) {
        StringBuilder sb = new StringBuilder(data.length * 2);
        for (byte b : data) {
            sb.append(String.format("%02x", b & 0xFF));
        }
        return sb.toString();
    }

    public static void main(String[] args) {
        byte[] enc = runEncryptionInVm();
        String encHex = bytesToHex(enc);

        if (args.length > 0 && "--hex".equals(args[0])) {
            System.out.println(encHex);
            return;
        }

        System.out.println("vm.enc.hex=" + encHex);
    }
}
