#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "aes128.h"
#include "vm.h"

#ifdef __linux__
#include <sys/ptrace.h>
#endif

static char input[128];
static char* p_input = input + 24; 
static uint8_t shadow_input[SHADOW_LEN];
static VMProgram g_prog;

static const uint8_t k_shadow_aes_key[16] = {
    0x2D, 0x7A, 0x4F, 0x19,
    0x88, 0xC1, 0x35, 0xE2,
    0x6B, 0x90, 0x14, 0xAF,
    0x53, 0xCD, 0x21, 0x77};

static const uint8_t k_expected_shadow_cipher[SHADOW_LEN] = {
    0x8E, 0xE4, 0xD5, 0x08, 0xE5, 0x8D, 0x5B, 0xD5, 0x69, 0xCE,
    0xE7, 0xFC, 0x93, 0xBD, 0x63, 0x9C, 0x54, 0xAB, 0x77, 0x81,
    0x30, 0xE4, 0x52, 0x83, 0x8C, 0x5B, 0x33, 0x57, 0xB7, 0x26,
    0xE2, 0xC2};

#ifdef __linux__
static void print_message_and_exit(const uint8_t *encoded_msg)
{
    while (*encoded_msg)
    {
        putchar((char)(*encoded_msg ^ 0x55u));
        ++encoded_msg;
    }
    putchar('\n');
    exit(EXIT_FAILURE);
}
#endif

__attribute__((constructor)) static void check_debugger(void)
{
#ifdef __linux__
    static const uint64_t encoded_message[] = {
        0x303D217521343D02ULL,
        0x3C3A3175323A3175ULL,
        0x00000000006A323BULL};

    if (ptrace(PTRACE_TRACEME, 0, NULL, NULL) == -1)
        print_message_and_exit((const uint8_t *)encoded_message);
#endif
}

__attribute__((destructor)) static void verify_flag(void)
{
    if(*(p_input - 24 + 32))
    {
        return;
    }
    vm_program_ensure_ready(&g_prog);

    VM vm;
    vm_init(&vm, &g_prog);

    memset(vm.mem, 0, sizeof(vm.mem));
    memcpy(vm.mem, input, REAL_FLAG_LEN);

    uint8_t target[REAL_TARGET_LEN];
    vm_build_real_target(target);
    memcpy(vm.mem + 0x80, target, sizeof(target));
    vm.mem[0xF0] = 0;

    vm_exec(&vm, &g_prog);

    if (vm.mem[0xF0] == 1)
        printf("%s\n", p_input - 24);
}

static void prepare_shadow_input(const char *src, uint8_t out[SHADOW_LEN])
{
    size_t n = strlen(src);
    if (n > SHADOW_LEN)
        n = SHADOW_LEN;

    memset(out, 0, SHADOW_LEN);

    for (size_t i = 0; i < SHADOW_LEN; ++i)
    {
        uint8_t base = (i < n) ? (uint8_t)src[i] : (uint8_t)(0x80u ^ (uint8_t)i);
        uint8_t pad = stream_byte(0x51A7BEEF, i);
        out[i] = (uint8_t)(base ^ pad ^ (uint8_t)(n + i * 3u));
    }

    out[0] ^= (uint8_t)n;
    out[SHADOW_LEN - 1] ^= (uint8_t)(n * 7u);
}

static void shadow_self_check(const uint8_t cipher[SHADOW_LEN])
{
    for (size_t i = 0; i < SHADOW_LEN; ++i)
    {
        if (cipher[i] != k_expected_shadow_cipher[i])
        {
            return;
        }
    }
    printf("Well, %.26s!\n", input + 5);
}

int main(void)
{
    printf("Input flag: ");
    if (scanf("%40s", input) != 1)
    {
        return 1;
    }

    if (strlen(input) != REAL_FLAG_LEN)
    {
        printf("Wrong length!\n");
        return 0;
    }

    prepare_shadow_input(input, shadow_input);
    aes128_encrypt_buffer(shadow_input, k_shadow_aes_key);
    shadow_self_check(shadow_input);

    return 0;
}
