#ifndef EZREVENGE_COMMON_H
#define EZREVENGE_COMMON_H

#include <stddef.h>
#include <stdint.h>

#define MEM_SIZE 512
#define REG_CNT 8
#define INSN_SIZE 4
#define REAL_FLAG_LEN 32
#define REAL_TARGET_LEN REAL_FLAG_LEN
#define SHADOW_LEN 32

#define TABLE_SIZE 4096
#define TABLE_MASK (TABLE_SIZE - 1)
#define MAX_STATES 4096
#define STEP_LIMIT 5000

static inline uint32_t rol32(uint32_t x, unsigned r)
{
    r &= 31u;
    return (x << r) | (x >> ((32u - r) & 31u));
}

static inline uint16_t imm16(uint8_t lo, uint8_t hi)
{
    return (uint16_t)(lo | ((uint16_t)hi << 8));
}

static inline uint8_t stream_byte(uint32_t seed, size_t idx)
{
    uint32_t x = seed + 0x9E3779B9u + (uint32_t)idx * 0x045D9F3Bu;
    x ^= rol32(seed ^ (uint32_t)idx, (unsigned)(idx & 7u));
    x ^= x >> 16;
    x *= 0x27D4EB2Du;
    x ^= x >> 15;
    return (uint8_t)(x & 0xFFu);
}

#endif
