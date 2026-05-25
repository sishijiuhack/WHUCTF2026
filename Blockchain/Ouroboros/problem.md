# Ouroboros

A private Ethereum-like chain hides a two-part flag inside a self-referential vault contract.

You are given:
- A JSON-RPC endpoint
- The deployed contract address
- Full source code (`Ouroboros.sol`)

Infrastructure note:
- Container exposes only one internal port: `8545` (JSON-RPC).
- GZCTF maps it to a random external port.
- Connect via `wsrx` or direct HTTP JSON-RPC to `localhost:<mapped_port>`.

## Goal
Recover the full flag in two stages:

1. **Forensic traceback (first half)**  
   The first half is not directly returned by any public getter.  
   You must reconstruct it by tracing deployment-era data (constructor/creation logs, nonce-based clues, etc.).

2. **Reentrancy cycle (second half)**  
   The second half is protected behind a reentrancy condition.  
   Only after completing a cyclic reentrant withdrawal can you call the reveal function to obtain it.

