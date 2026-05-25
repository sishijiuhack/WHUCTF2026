#!/usr/bin/env bash
set -euo pipefail

RPC_URL="${RPC_URL:-http://127.0.0.1:8545}"
MAX_TRIES="${MAX_TRIES:-20}"
SLEEP_SECS="${SLEEP_SECS:-1}"
export FOUNDRY_DISABLE_NIGHTLY_WARNING=1

echo "[selfcheck] RPC URL: ${RPC_URL}"

ok_cast=0
ok_curl=0
last_cast=""
last_curl=""

for i in $(seq 1 "${MAX_TRIES}"); do
    if out_cast="$(cast rpc --rpc-url "${RPC_URL}" eth_chainId 2>/dev/null)"; then
        last_cast="${out_cast}"
        ok_cast=1
    fi

    if out_curl="$(
        curl -sS -m 3 -H "Content-Type: application/json" \
            -d '{"jsonrpc":"2.0","id":1,"method":"eth_chainId","params":[]}' \
            "${RPC_URL}" 2>/dev/null || true
    )"; then
        if [[ "${out_curl}" == *"\"result\""* ]]; then
            last_curl="${out_curl}"
            ok_curl=1
        fi
    fi

    if [[ "${ok_cast}" -eq 1 && "${ok_curl}" -eq 1 ]]; then
        break
    fi

    sleep "${SLEEP_SECS}"
done

if [[ "${ok_cast}" -eq 1 ]]; then
    echo "[selfcheck] cast eth_chainId OK: ${last_cast}"
else
    echo "[selfcheck] cast eth_chainId FAILED"
fi

if [[ "${ok_curl}" -eq 1 ]]; then
    echo "[selfcheck] curl eth_chainId OK: ${last_curl}"
else
    echo "[selfcheck] curl eth_chainId FAILED"
fi

if [[ "${ok_cast}" -eq 1 && "${ok_curl}" -eq 1 ]]; then
    echo "[selfcheck] RPC health: PASS"
    exit 0
fi

echo "[selfcheck] RPC health: FAIL"
exit 1
