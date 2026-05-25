FROM ghcr.io/foundry-rs/foundry:latest

USER root

RUN apt-get update \
    && apt-get install -y --no-install-recommends bash python3 jq ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -u 10001 ctf

WORKDIR /home/ctf
COPY Ouroboros.sol /home/ctf/Ouroboros.sol
COPY deploy.sh /home/ctf/deploy.sh
COPY rpc_selfcheck.sh /home/ctf/rpc_selfcheck.sh
COPY foundry.toml /home/ctf/foundry.toml
COPY problem.md /home/ctf/problem.md
COPY solution.md /home/ctf/solution.md

RUN chmod +x /home/ctf/deploy.sh \
    && chmod +x /home/ctf/rpc_selfcheck.sh \
    && chown -R ctf:ctf /home/ctf

USER ctf
EXPOSE 8545

ENTRYPOINT ["/home/ctf/deploy.sh"]
