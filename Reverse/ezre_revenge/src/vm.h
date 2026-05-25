#ifndef EZREVENGE_VM_H
#define EZREVENGE_VM_H

#include "common.h"

typedef struct
{
    uint32_t reg[REG_CNT];
    uint8_t mem[MEM_SIZE];
    uint16_t sid;
    uint16_t branch_sid;
    uint32_t step;
    uint32_t kstate;
    uint32_t cstate;
    uint32_t trap;
    uint8_t zf;
    uint8_t running;
    uint8_t branch_override;
} VM;

typedef struct
{
    size_t state_count;
    uint16_t start_sid;
    uint16_t halt_sid;
    uint16_t logical_to_sid[MAX_STATES];
    uint16_t sid_to_slot[TABLE_SIZE];
    uint16_t edge_token[TABLE_SIZE];
    uint16_t state_table[TABLE_SIZE];
    uint16_t inv_state_table[TABLE_SIZE];
    uint8_t enc_code[MAX_STATES * INSN_SIZE];
    uint8_t built;
} VMProgram;

void vm_program_ensure_ready(VMProgram *program);
void vm_build_real_target(uint8_t out[REAL_TARGET_LEN]);
void vm_init(VM *vm, const VMProgram *program);
void vm_exec(VM *vm, const VMProgram *program);

#endif
