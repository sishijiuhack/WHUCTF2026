#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <stdlib.h>
#include <sys/ptrace.h>

#define MEM_SIZE 512
#define REG_CNT 8

typedef struct
{
    uint32_t reg[REG_CNT];
    uint8_t mem[MEM_SIZE];
    uint32_t pc;
    uint8_t zf;
    uint8_t running;
} VM;

/*
 * 定长 4 字节指令:
 * [opcode][op1][op2][op3]
 *
 * 指令集：
 * 0x01 MOVI   reg[op1] = op2
 * 0x02 LOAD   reg[op1] = mem[op2]
 * 0x03 STORE  mem[op2] = reg[op1]
 * 0x04 ADD    reg[op1] += reg[op2]
 * 0x05 ADDI   reg[op1] += op2
 * 0x06 XORI   reg[op1] ^= op2
 * 0x07 SHL    reg[op1] <<= op2
 * 0x08 SHR    reg[op1] >>= op2
 * 0x09 CMP    zf = (reg[op1] == reg[op2])
 * 0x0A JNZ    if (!zf) pc = op1
 * 0x0B JMP    pc = op1
 * 0x0C HALT   running = 0
 * 0x0D LOADR  reg[op1] = mem[reg[op2]]
 * 0x0E STORER mem[reg[op2]] = reg[op1]
 * 0x0F INCR   reg[op1]++
 */

enum
{
    OP_MOVI = 0x01,
    OP_LOAD = 0x02,
    OP_STORE = 0x03,
    OP_ADD = 0x04,
    OP_ADDI = 0x05,
    OP_XORI = 0x06,
    OP_SHL = 0x07,
    OP_SHR = 0x08,
    OP_CMP = 0x09,
    OP_JNZ = 0x0A,
    OP_JMP = 0x0B,
    OP_HALT = 0x0C,
    OP_LOADR = 0x0D,
    OP_STORER = 0x0E,
    OP_INCR = 0x0F
};

char input[128];
char* input_ptr = input + 10;

static void vm_init(VM* vm)
{
    memset(vm, 0, sizeof(VM));
    vm->running = 1;
}

static void vm_exec(VM* vm, const uint8_t* code, size_t code_size)
{
    while (vm->running)
    {
        if ((vm->pc * 4) >= code_size)
        {
            vm->running = 0;
            break;
        }

        uint8_t opcode = code[vm->pc * 4];
        uint8_t op1 = code[vm->pc * 4 + 1];
        uint8_t op2 = code[vm->pc * 4 + 2];
        uint8_t op3 = code[vm->pc * 4 + 3];

        (void)op3;

        switch (opcode)
        {
        case OP_MOVI:
            if (op1 < REG_CNT)
                vm->reg[op1] = op2;
            vm->pc++;
            break;

        case OP_LOAD:
            if (op1 < REG_CNT && op2 < MEM_SIZE)
                vm->reg[op1] = vm->mem[op2];
            vm->pc++;
            break;

        case OP_STORE:
            if (op1 < REG_CNT && op2 < MEM_SIZE)
                vm->mem[op2] = (uint8_t)(vm->reg[op1] & 0xFF);
            vm->pc++;
            break;

        case OP_ADD:
            if (op1 < REG_CNT && op2 < REG_CNT)
                vm->reg[op1] += vm->reg[op2];
            vm->pc++;
            break;

        case OP_ADDI:
            if (op1 < REG_CNT)
                vm->reg[op1] += op2;
            vm->pc++;
            break;

        case OP_XORI:
            if (op1 < REG_CNT)
                vm->reg[op1] ^= op2;
            vm->pc++;
            break;

        case OP_SHL:
            if (op1 < REG_CNT)
                vm->reg[op1] <<= op2;
            vm->pc++;
            break;

        case OP_SHR:
            if (op1 < REG_CNT)
                vm->reg[op1] >>= op2;
            vm->pc++;
            break;

        case OP_CMP:
            if (op1 < REG_CNT && op2 < REG_CNT)
                vm->zf = (vm->reg[op1] == vm->reg[op2]) ? 1 : 0;
            else
                vm->zf = 0;
            vm->pc++;
            break;

        case OP_JNZ:
            if (!vm->zf)
                vm->pc = op1;
            else
                vm->pc++;
            break;

        case OP_JMP:
            vm->pc = op1;
            break;

        case OP_HALT:
            vm->running = 0;
            break;

        case OP_LOADR:
            if (op1 < REG_CNT && op2 < REG_CNT && vm->reg[op2] < MEM_SIZE)
                vm->reg[op1] = vm->mem[vm->reg[op2]];
            vm->pc++;
            break;

        case OP_STORER:
            if (op1 < REG_CNT && op2 < REG_CNT && vm->reg[op2] < MEM_SIZE)
                vm->mem[vm->reg[op2]] = (uint8_t)(vm->reg[op1] & 0xFF);
            vm->pc++;
            break;

        case OP_INCR:
            if (op1 < REG_CNT)
                vm->reg[op1]++;
            vm->pc++;
            break;

        default:
            vm->running = 0;
            break;
        }
    }
}

__attribute__((constructor)) void check_debugger(void)
{
    if (ptrace(PTRACE_TRACEME, 0, NULL, NULL) == -1)
    {
        exit(1);
    }
}

__attribute__((destructor)) void verify_flag()
{
    VM vm;
    vm_init(&vm);

    /*
     * 变换:
     * t = (((c + 3) ^ 0x5A) + i) & 0xFF
     */
    const int flag_len = 18;

    const uint8_t target[18] = {
        51, 54, 64, 51, 40, 8, 16, 63, 118, 53, 66, 23, 117, 69, 64, 54, 142, 235 };

    /*
     * 内存布局：
     * 0x00 ~ 0x11 : 输入
     * 0x80 ~ 0x91 : target
     * 0xF0        : 校验结果
     */

    memset(vm.mem, 0, sizeof(vm.mem));
    memcpy(vm.mem, input_ptr - 10, flag_len);
    memcpy(vm.mem + 0x80, target, flag_len);
    vm.mem[0xF0] = 1;

    /*
     * 寄存器约定：
     * r0: 当前输入字节 / 临时
     * r1: 当前目标字节 / 临时
     * r2: 输入地址指针
     * r3: 目标地址指针
     * r4: 循环计数 i
     * r5: flag_len
     * r6: 常量 0
     * r7: 临时结果位
     *
     * 字节码逻辑：
     *   r2 = 0x00
     *   r3 = 0x80
     *   r4 = 0
     *   r5 = 18
     *
     * loop:
     *   r0 = mem[r2]
     *   r0 += 3
     *   r0 ^= 0x5A
     *   r0 += r4
     *   r1 = mem[r3]
     *   cmp r0, r1
     *   if != : mem[0xF0] = 0
     * next:
     *   r2++
     *   r3++
     *   r4++
     *   cmp r4, r5
     *   if != goto loop
     *   halt
     */

    static const uint8_t bytecode[] = {
        /* 0  */ OP_MOVI, 2, 0x00, 0, // r2 = 0x00
        /* 1  */ OP_MOVI, 3, 0x80, 0, // r3 = 0x80
        /* 2  */ OP_MOVI, 4, 0x00, 0, // r4 = 0
        /* 3  */ OP_MOVI, 5, 18, 0,   // r5 = 18
        /* 4  */ OP_MOVI, 6, 0x00, 0, // r6 = 0

        /* loop: */
        /* 5  */ OP_LOADR, 0, 2, 0,   // r0 = mem[r2]
        /* 6  */ OP_ADDI, 0, 0x03, 0, // r0 += 3
        /* 7  */ OP_XORI, 0, 0x5A, 0, // r0 ^= 0x5A
        /* 8  */ OP_ADD, 0, 4, 0,     // r0 += r4
        /* 9  */ OP_LOADR, 1, 3, 0,   // r1 = mem[r3]
        /* 10 */ OP_CMP, 0, 1, 0,     // zf = (r0 == r1)
        /* 11 */ OP_JNZ, 13, 0, 0,    // if != goto mismatch
        /* 12 */ OP_JMP, 15, 0, 0,    // goto next

        /* mismatch: */
        /* 13 */ OP_MOVI, 7, 0x00, 0,  // r7 = 0
        /* 14 */ OP_STORE, 7, 0xF0, 0, // mem[0xF0] = 0

        /* next: */
        /* 15 */ OP_INCR, 2, 0, 0, // r2++
        /* 16 */ OP_INCR, 3, 0, 0, // r3++
        /* 17 */ OP_INCR, 4, 0, 0, // r4++
        /* 18 */ OP_CMP, 4, 5, 0,  // i == flag_len ?
        /* 19 */ OP_JNZ, 5, 0, 0,  // if != goto loop
        /* 20 */ OP_HALT, 0, 0, 0 };

    vm_exec(&vm, bytecode, sizeof(bytecode));

    if (vm.mem[0xF0] == 1)
        printf("%.6s\n", input_ptr + 1);
}

static volatile uint32_t g_noise_sink = 0;

static uint32_t noise_mix(uint32_t x)
{
    x ^= 0x9E3779B9u;
    x += (x << 7) ^ (x >> 3);
    x ^= 0xA5A5A5A5u;
    x = (x << 11) | (x >> 21);
    x += 0x13579BDFu;
    x ^= (x >> 16);
    return x;
}

static void noise_vm_like(const char* buf)
{
    uint32_t s = 0x55;
    for (size_t i = 0; buf[i]; ++i)
    {
        switch ((buf[i] + i + s) & 3)
        {
        case 0:
            s ^= ((unsigned char)buf[i] << 1);
            break;
        case 1:
            s += ((unsigned char)buf[i] ^ 0x3A);
            break;
        case 2:
            s = (s << 3) | (s >> 29);
            break;
        default:
            s -= (unsigned char)buf[i];
            break;
        }
    }
    g_noise_sink ^= s;
}

static void noise_table(const char* buf)
{
    static const uint8_t tbl[16] = {
        0x13, 0x37, 0xC0, 0xDE,
        0x42, 0x99, 0xAB, 0x5E,
        0x71, 0x28, 0x6D, 0x84,
        0xFA, 0x11, 0x22, 0x33 };

    uint32_t acc = 0;
    for (size_t i = 0; buf[i]; ++i)
    {
        acc += tbl[((unsigned char)buf[i] ^ i) & 0xF];
        acc ^= noise_mix(acc + i);
    }
    g_noise_sink += acc;
}

static void noise_fake_check(const char* buf)
{
    uint32_t x = 0xDEADBEEFu;
    uint32_t y = 0x12345678u;

    for (size_t i = 0; buf[i]; ++i)
    {
        x = noise_mix(x + (unsigned char)buf[i]);
        y ^= (x >> ((i & 3) * 8));
    }

    /* 不透明谓词，结果对主逻辑无影响 */
    if (((x ^ y) & 0xFFu) == 0x42u)
        g_noise_sink ^= 0xCAFEBABEu;
    else
        g_noise_sink += 0x10203040u;
}

int main()
{
    printf("Input flag: ");
    scanf("%s", input);

    noise_vm_like(input);
    noise_table(input);
    noise_fake_check(input);

    return 0;
}