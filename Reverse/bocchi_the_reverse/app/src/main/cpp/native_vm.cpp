#include <jni.h>

#include <algorithm>
#include <cstdint>
#include <cstring>
#include <iterator>
#include <mutex>
#include <sstream>
#include <string>
#include <string_view>
#include <vector>

namespace {

constexpr int kTextBase = 0x0000;
constexpr int kKeyBase = 0x0100;
constexpr int kRoundKeyBase = 0x0200;
constexpr int kCkBase = 0x0300;
constexpr int kSboxBase = 0x0500;
constexpr int kCodeBase = 0x1000;
constexpr int kInstrSize = 8;
constexpr int kMemorySize = 0x8000;
constexpr int kRegisterCount = 16;
constexpr int kStackSize = 1024;
constexpr int kProgramEntry = 0x1130;
constexpr int kEmbeddedSboxSize = 256;
constexpr int kOuterLoopBlockCountInstr = 0x14e8;

constexpr char kProgramBlobBase64[] =
    "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"
    "8BAAAAAAAAAA==";

struct VmState {
    int32_t regs[kRegisterCount] = {};
    int32_t stack[kStackSize] = {};
    int32_t sp = 0;
    int32_t ip = 0;
    int32_t cmp = 0;
    bool halted = false;
    int32_t codeSize = 0;
    std::vector<uint8_t> memory = std::vector<uint8_t>(kMemorySize, 0);
};

VmState gVm;
std::mutex gMutex;

void ThrowIllegalState(JNIEnv* env, const char* message) {
    jclass exClass = env->FindClass("java/lang/IllegalStateException");
    if (exClass != nullptr) {
        env->ThrowNew(exClass, message);
        env->DeleteLocalRef(exClass);
    }
}

int DecodeBase64Char(char ch) {
    if (ch >= 'A' && ch <= 'Z') {
        return ch - 'A';
    }
    if (ch >= 'a' && ch <= 'z') {
        return ch - 'a' + 26;
    }
    if (ch >= '0' && ch <= '9') {
        return ch - '0' + 52;
    }
    if (ch == '+') {
        return 62;
    }
    if (ch == '/') {
        return 63;
    }
    return -1;
}

std::vector<uint8_t> DecodeBase64(std::string_view encoded) {
    std::vector<uint8_t> out;
    out.reserve(encoded.size() * 3 / 4);

    int accumulator = 0;
    int bits = -8;
    for (char ch : encoded) {
        if (ch == '=') {
            break;
        }
        const int value = DecodeBase64Char(ch);
        if (value < 0) {
            continue;
        }
        accumulator = (accumulator << 6) | value;
        bits += 6;
        if (bits >= 0) {
            out.push_back(static_cast<uint8_t>((accumulator >> bits) & 0xFF));
            bits -= 8;
        }
    }
    return out;
}

const std::vector<uint8_t>& ProgramBlob() {
    static const std::vector<uint8_t> blob = DecodeBase64(kProgramBlobBase64);
    return blob;
}

void CheckRange(JNIEnv* env, int addr, int len) {
    if (addr < 0 || len < 0 || addr + len > static_cast<int>(gVm.memory.size())) {
        ThrowIllegalState(env, "Memory out of range");
    }
}

void CheckRegister(JNIEnv* env, int index) {
    if (index < 0 || index >= kRegisterCount) {
        ThrowIllegalState(env, "Register index out of range");
    }
}

void CheckStackIndex(JNIEnv* env, int index) {
    if (index < 0 || index >= kStackSize) {
        ThrowIllegalState(env, "Stack index out of range");
    }
}

int32_t ReadU32BE(int addr) {
    return static_cast<int32_t>(
        (static_cast<uint32_t>(gVm.memory[addr]) << 24) |
        (static_cast<uint32_t>(gVm.memory[addr + 1]) << 16) |
        (static_cast<uint32_t>(gVm.memory[addr + 2]) << 8) |
        static_cast<uint32_t>(gVm.memory[addr + 3])
    );
}

void WriteU32BE(int addr, int32_t value) {
    const uint32_t raw = static_cast<uint32_t>(value);
    gVm.memory[addr] = static_cast<uint8_t>((raw >> 24) & 0xFF);
    gVm.memory[addr + 1] = static_cast<uint8_t>((raw >> 16) & 0xFF);
    gVm.memory[addr + 2] = static_cast<uint8_t>((raw >> 8) & 0xFF);
    gVm.memory[addr + 3] = static_cast<uint8_t>(raw & 0xFF);
}

void WriteI32LE(int addr, int32_t value) {
    const uint32_t raw = static_cast<uint32_t>(value);
    gVm.memory[addr] = static_cast<uint8_t>(raw & 0xFF);
    gVm.memory[addr + 1] = static_cast<uint8_t>((raw >> 8) & 0xFF);
    gVm.memory[addr + 2] = static_cast<uint8_t>((raw >> 16) & 0xFF);
    gVm.memory[addr + 3] = static_cast<uint8_t>((raw >> 24) & 0xFF);
}

std::string ReadInstructionContextLocked(JNIEnv* env, int ip) {
    if (ip < kCodeBase || ip + kInstrSize > kCodeBase + gVm.codeSize) {
        ThrowIllegalState(env, "IP out of code range");
        return {};
    }

    const uint8_t opcode = gVm.memory[ip];
    const int a = gVm.memory[ip + 1] & 0xFF;
    const int b = gVm.memory[ip + 2] & 0xFF;
    const int c = gVm.memory[ip + 3] & 0xFF;
    const int32_t imm = static_cast<int32_t>(
        (static_cast<uint32_t>(gVm.memory[ip + 4])) |
        (static_cast<uint32_t>(gVm.memory[ip + 5]) << 8) |
        (static_cast<uint32_t>(gVm.memory[ip + 6]) << 16) |
        (static_cast<uint32_t>(gVm.memory[ip + 7]) << 24)
    );

    std::ostringstream oss;
    oss << "{"
        << "\"ip\":" << ip
        << ",\"opcodeValue\":" << static_cast<int>(opcode)
        << ",\"a\":" << a
        << ",\"b\":" << b
        << ",\"c\":" << c
        << ",\"imm\":" << imm;

    switch (opcode) {
        case 0x03:
            oss << ",\"srcValue\":" << gVm.regs[b];
            break;
        case 0x04: {
            const int addr = gVm.regs[b] + imm;
            CheckRange(env, addr, 4);
            if (env->ExceptionCheck()) {
                return {};
            }
            oss << ",\"addr\":" << addr
                << ",\"value\":" << ReadU32BE(addr);
            break;
        }
        case 0x05: {
            const int addr = gVm.regs[b] + imm;
            CheckRange(env, addr, 4);
            if (env->ExceptionCheck()) {
                return {};
            }
            oss << ",\"addr\":" << addr
                << ",\"value\":" << gVm.regs[a];
            break;
        }
        case 0x06:
            oss << ",\"lhs\":" << gVm.regs[b]
                << ",\"rhs\":" << gVm.regs[c];
            break;
        case 0x07:
        case 0x08:
        case 0x09:
        case 0x0A:
        case 0x0B:
        case 0x0C:
            oss << ",\"srcValue\":" << gVm.regs[b];
            break;
        case 0x0D:
            oss << ",\"lhs\":" << gVm.regs[a]
                << ",\"rhs\":" << gVm.regs[b];
            break;
        case 0x0F:
            oss << ",\"cmpValue\":" << gVm.cmp;
            break;
        case 0x10:
            oss << ",\"sp\":" << gVm.sp
                << ",\"value\":" << gVm.regs[a];
            break;
        case 0x11:
            if (gVm.sp <= 0) {
                ThrowIllegalState(env, "Stack underflow");
                return {};
            }
            oss << ",\"sp\":" << gVm.sp
                << ",\"value\":" << gVm.stack[gVm.sp - 1];
            break;
        case 0x12: {
            const int base = gVm.regs[c];
            const int idx = gVm.regs[b] & 0xFF;
            const int addr = base + idx;
            CheckRange(env, addr, 1);
            if (env->ExceptionCheck()) {
                return {};
            }
            oss << ",\"idx\":" << idx
                << ",\"base\":" << base
                << ",\"addr\":" << addr
                << ",\"value\":" << static_cast<int>(gVm.memory[addr]);
            break;
        }
        default:
            break;
    }

    oss << "}";
    return oss.str();
}

std::string ReadHexLocked(JNIEnv* env, int addr, int len) {
    CheckRange(env, addr, len);
    if (env->ExceptionCheck()) {
        return {};
    }
    static const char* kHex = "0123456789abcdef";
    std::string out;
    out.reserve(static_cast<size_t>(len) * 2);
    for (int i = 0; i < len; ++i) {
        const uint8_t value = gVm.memory[addr + i];
        out.push_back(kHex[(value >> 4) & 0xF]);
        out.push_back(kHex[value & 0xF]);
    }
    return out;
}

void NativeReset(JNIEnv* env, jclass, jint blockCount) {
    std::lock_guard<std::mutex> lock(gMutex);

    if (blockCount <= 0) {
        ThrowIllegalState(env, "Block count must be positive");
    }

    const std::vector<uint8_t>& blob = ProgramBlob();
    if (blob.size() <= static_cast<size_t>(kEmbeddedSboxSize)) {
        ThrowIllegalState(env, "Program blob is too small");
    }

    const int programLen = static_cast<int>(blob.size()) - kEmbeddedSboxSize;
    if (kCodeBase + programLen > kMemorySize) {
        ThrowIllegalState(env, "Program is too large");
    }

    std::fill(std::begin(gVm.regs), std::end(gVm.regs), 0);
    std::fill(std::begin(gVm.stack), std::end(gVm.stack), 0);
    std::fill(gVm.memory.begin(), gVm.memory.end(), 0);

    std::memcpy(gVm.memory.data() + kSboxBase, blob.data(), kEmbeddedSboxSize);
    std::memcpy(gVm.memory.data() + kCodeBase, blob.data() + kEmbeddedSboxSize, static_cast<size_t>(programLen));

    gVm.sp = 0;
    gVm.ip = kProgramEntry;
    gVm.cmp = 0;
    gVm.halted = false;
    gVm.codeSize = programLen;

    gVm.regs[10] = kTextBase;
    gVm.regs[11] = kKeyBase;
    gVm.regs[12] = kRoundKeyBase;
    gVm.regs[6] = kCkBase;
    gVm.regs[13] = kSboxBase;
    gVm.regs[7] = kRoundKeyBase;

    WriteI32LE(kOuterLoopBlockCountInstr + 4, blockCount);
}

jint NativeGetIp(JNIEnv*, jclass) {
    std::lock_guard<std::mutex> lock(gMutex);
    return gVm.ip;
}

jboolean NativeIsHalted(JNIEnv*, jclass) {
    std::lock_guard<std::mutex> lock(gMutex);
    return gVm.halted ? JNI_TRUE : JNI_FALSE;
}

jstring NativeReadInstructionContext(JNIEnv* env, jclass, jint ip) {
    std::lock_guard<std::mutex> lock(gMutex);
    const std::string json = ReadInstructionContextLocked(env, ip);
    if (env->ExceptionCheck()) {
        return nullptr;
    }
    return env->NewStringUTF(json.c_str());
}

void NativeSetIp(JNIEnv* env, jclass, jint ip) {
    std::lock_guard<std::mutex> lock(gMutex);
    if (ip < 0 || ip >= kMemorySize) {
        ThrowIllegalState(env, "IP out of range");
    }
    gVm.ip = ip;
}

void NativeSetCmp(JNIEnv*, jclass, jint cmp) {
    std::lock_guard<std::mutex> lock(gMutex);
    gVm.cmp = cmp;
}

void NativeSetHalted(JNIEnv*, jclass, jboolean halted) {
    std::lock_guard<std::mutex> lock(gMutex);
    gVm.halted = halted == JNI_TRUE;
}

void NativeSetSp(JNIEnv* env, jclass, jint sp) {
    std::lock_guard<std::mutex> lock(gMutex);
    if (sp < 0 || sp > kStackSize) {
        ThrowIllegalState(env, "SP out of range");
    }
    gVm.sp = sp;
}

void NativeSetRegister(JNIEnv* env, jclass, jint index, jint value) {
    std::lock_guard<std::mutex> lock(gMutex);
    CheckRegister(env, index);
    gVm.regs[index] = value;
}

void NativeSetStackValue(JNIEnv* env, jclass, jint index, jint value) {
    std::lock_guard<std::mutex> lock(gMutex);
    CheckStackIndex(env, index);
    gVm.stack[index] = value;
}

void NativeWriteMemoryU32BE(JNIEnv* env, jclass, jint addr, jint value) {
    std::lock_guard<std::mutex> lock(gMutex);
    CheckRange(env, addr, 4);
    WriteU32BE(addr, value);
}

void NativeWriteUtf8ToMemory(JNIEnv* env, jclass, jint addr, jstring value) {
    std::lock_guard<std::mutex> lock(gMutex);

    if (value == nullptr) {
        ThrowIllegalState(env, "String value is null");
    }

    const char* raw = env->GetStringUTFChars(value, nullptr);
    const jsize len = env->GetStringUTFLength(value);
    CheckRange(env, addr, len);
    std::memcpy(gVm.memory.data() + addr, raw, static_cast<size_t>(len));
    env->ReleaseStringUTFChars(value, raw);
}

jstring NativeReadMemoryHex(JNIEnv* env, jclass, jint addr, jint len) {
    std::lock_guard<std::mutex> lock(gMutex);
    const std::string hex = ReadHexLocked(env, addr, len);
    if (env->ExceptionCheck()) {
        return nullptr;
    }
    return env->NewStringUTF(hex.c_str());
}

const JNINativeMethod kNativeMethods[] = {
    {"nativeReset", "(I)V", reinterpret_cast<void*>(NativeReset)},
    {"nativeGetIp", "()I", reinterpret_cast<void*>(NativeGetIp)},
    {"nativeIsHalted", "()Z", reinterpret_cast<void*>(NativeIsHalted)},
    {"nativeReadInstructionContext", "(I)Ljava/lang/String;", reinterpret_cast<void*>(NativeReadInstructionContext)},
    {"nativeSetIp", "(I)V", reinterpret_cast<void*>(NativeSetIp)},
    {"nativeSetCmp", "(I)V", reinterpret_cast<void*>(NativeSetCmp)},
    {"nativeSetHalted", "(Z)V", reinterpret_cast<void*>(NativeSetHalted)},
    {"nativeSetSp", "(I)V", reinterpret_cast<void*>(NativeSetSp)},
    {"nativeSetRegister", "(II)V", reinterpret_cast<void*>(NativeSetRegister)},
    {"nativeSetStackValue", "(II)V", reinterpret_cast<void*>(NativeSetStackValue)},
    {"nativeWriteMemoryU32BE", "(II)V", reinterpret_cast<void*>(NativeWriteMemoryU32BE)},
    {"nativeWriteUtf8ToMemory", "(ILjava/lang/String;)V", reinterpret_cast<void*>(NativeWriteUtf8ToMemory)},
    {"nativeReadMemoryHex", "(II)Ljava/lang/String;", reinterpret_cast<void*>(NativeReadMemoryHex)},
};

}  // namespace

extern "C" __attribute__((visibility("default"))) jint JNI_OnLoad(JavaVM* vm, void*) {
    JNIEnv* env = nullptr;
    if (vm->GetEnv(reinterpret_cast<void**>(&env), JNI_VERSION_1_6) != JNI_OK || env == nullptr) {
        return JNI_ERR;
    }

    jclass bridgeClass = env->FindClass("com/example/bocchi_the_reverse/NativeVmBridge");
    if (bridgeClass == nullptr) {
        return JNI_ERR;
    }

    const jint result = env->RegisterNatives(
        bridgeClass,
        kNativeMethods,
        static_cast<jint>(std::size(kNativeMethods))
    );
    env->DeleteLocalRef(bridgeClass);
    if (result != JNI_OK) {
        return JNI_ERR;
    }

    return JNI_VERSION_1_6;
}
