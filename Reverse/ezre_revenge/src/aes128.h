#ifndef EZREVENGE_AES128_H
#define EZREVENGE_AES128_H

#include "common.h"

void aes128_encrypt_buffer(uint8_t buf[SHADOW_LEN], const uint8_t key[16]);

#endif
