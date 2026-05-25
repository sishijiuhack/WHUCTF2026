#!/usr/bin/env bash
set -euo pipefail

RPC_PORT="${RPC_PORT:-8545}"
CHAIN_ID="${CHAIN_ID:-31337}"
TREASURY_ETH="${TREASURY_ETH:-30}"
export FOUNDRY_DISABLE_NIGHTLY_WARNING=1

# Anvil default first private key (well-known in CTF/private local chains).
DEPLOYER_PK="${DEPLOYER_PK:-0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80}"
FLAG="${GZCTF_FLAG:-flag{ouroboros_demo_flag}}"

WORKDIR="/home/ctf"
RPC_URL="http://127.0.0.1:${RPC_PORT}"
ANVIL_LOG="/tmp/anvil.log"

echo "[*] Starting Anvil on 0.0.0.0:${RPC_PORT}..."
anvil --host 0.0.0.0 --port "${RPC_PORT}" --chain-id "${CHAIN_ID}" >"${ANVIL_LOG}" 2>&1 &
ANVIL_PID=$!

cleanup() {
    if kill -0 "${ANVIL_PID}" >/dev/null 2>&1; then
        kill "${ANVIL_PID}" >/dev/null 2>&1 || true
    fi
}
trap cleanup EXIT

for _ in $(seq 1 120); do
    if cast chain-id --rpc-url "${RPC_URL}" >/dev/null 2>&1; then
        break
    fi
    sleep 0.5
done
cast chain-id --rpc-url "${RPC_URL}" >/dev/null 2>&1

readarray -t FLAG_PARTS < <(python3 - <<'PY'
import os
flag = os.environ.get("GZCTF_FLAG", "flag{ouroboros_demo_flag}")
mid = len(flag) // 2
first = flag[:mid]
second = flag[mid:]
print(first)
print(second)
print("0x" + first.encode().hex())
print("0x" + second.encode().hex())
PY
)

FIRST_HALF="${FLAG_PARTS[0]}"
SECOND_HALF="${FLAG_PARTS[1]}"
FIRST_HEX="${FLAG_PARTS[2]}"
SECOND_HEX="${FLAG_PARTS[3]}"

DEPLOYER_ADDR="$(cast wallet address --private-key "${DEPLOYER_PK}")"
DEPLOY_NONCE="$(cast nonce "${DEPLOYER_ADDR}" --rpc-url "${RPC_URL}")"

HEAD_MASK="$(
    cast keccak "$(
        cast abi-encode "f(address,uint64,string)" "${DEPLOYER_ADDR}" "${DEPLOY_NONCE}" "ouroboros-head"
    )"
)"

COILED_HEAD="$(python3 - "${FIRST_HEX}" "${HEAD_MASK}" <<'PY'
import sys
data = bytes.fromhex(sys.argv[1][2:])
mask = bytes.fromhex(sys.argv[2][2:])
out = bytes([b ^ mask[i % len(mask)] for i, b in enumerate(data)])
print("0x" + out.hex())
PY
)"

FIRST_COMMITMENT="$(cast keccak "${FIRST_HEX}")"
CONSTRUCTOR_ARGS_FILE="/tmp/ouroboros_ctor_args.txt"
{
    echo "${COILED_HEAD}"
    echo "${DEPLOY_NONCE}"
    echo "${FIRST_COMMITMENT}"
} >"${CONSTRUCTOR_ARGS_FILE}"

echo "[*] Building contract..."
forge build >/tmp/forge-build.log

echo "[*] Deploying Ouroboros..."
if ! DEPLOY_OUTPUT="$(
    forge create Ouroboros.sol:Ouroboros \
        --rpc-url "${RPC_URL}" \
        --private-key "${DEPLOYER_PK}" \
        --constructor-args-path "${CONSTRUCTOR_ARGS_FILE}" \
        --value "${TREASURY_ETH}ether" \
        --broadcast 2>&1
)"; then
    echo "${DEPLOY_OUTPUT}"
    echo "[!] forge create failed"
    exit 1
fi
echo "${DEPLOY_OUTPUT}"

CONTRACT_ADDR="$(echo "${DEPLOY_OUTPUT}" | awk '/Deployed to:/{print $3}' | tail -n1)"
DEPLOY_TX_HASH="$(echo "${DEPLOY_OUTPUT}" | awk '/Transaction hash:/{print $3}' | tail -n1)"

if [[ -z "${CONTRACT_ADDR}" || -z "${DEPLOY_TX_HASH}" ]]; then
    echo "[!] Deployment output parse failed"
    exit 1
fi

echo "[*] Seeding second half..."
cast send "${CONTRACT_ADDR}" "setTail(string)" "${SECOND_HALF}" \
    --private-key "${DEPLOYER_PK}" --rpc-url "${RPC_URL}" >/tmp/set-tail.log

cat >"${WORKDIR}/instance.txt" <<EOF
Challenge: Ouroboros
RPC: http://<host>:${RPC_PORT}
Contract: ${CONTRACT_ADDR}
EOF

echo "[+] Ouroboros deployed"
echo "[+] Contract: ${CONTRACT_ADDR}"
echo "[+] Deployer: ${DEPLOYER_ADDR}"
echo "[+] Nonce hint: ${DEPLOY_NONCE}"
echo "[+] First half length: ${#FIRST_HALF}"
echo "[+] Second half length: ${#SECOND_HALF}"
echo "[+] Instance info written to ${WORKDIR}/instance.txt"

# Local health check inside container, useful to distinguish node issues from forwarding issues.
if /home/ctf/rpc_selfcheck.sh; then
    echo "[+] RPC selfcheck passed"
else
    echo "[!] RPC selfcheck failed"
fi

# Keep JSON-RPC available for players.
wait "${ANVIL_PID}"
