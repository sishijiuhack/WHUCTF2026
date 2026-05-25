// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

contract Ouroboros {
    mapping(address => uint256) public balances;
    mapping(address => uint256) public loopDepth;
    mapping(address => bool) public tailUnlocked;

    address public immutable shedder;
    uint64 public immutable birthNonce;
    uint256 public immutable initialTreasury;
    bytes32 public immutable firstHalfCommitment;

    string private tail;

    bool private insideWithdraw;
    address private currentCycler;
    bool public tailConfigured;

    event GenesisTrace(bytes coiledHead, uint64 birthNonce, address indexed shedder);
    event Deposit(address indexed from, uint256 amount);
    event Loop(address indexed player, uint256 depth, uint256 vaultBalance);
    event TailUnlockedFor(address indexed player, uint256 depth);
    event TailRevealed(address indexed player, string tail);

    modifier onlyShedder() {
        require(msg.sender == shedder, "not shedder");
        _;
    }
    constructor(bytes memory coiledHead, uint64 _birthNonce, bytes32 _firstHalfCommitment) payable {
        shedder = msg.sender;
        birthNonce = _birthNonce;
        firstHalfCommitment = _firstHalfCommitment;
        initialTreasury = msg.value;
        emit GenesisTrace(coiledHead, _birthNonce, msg.sender);
    }

    function setTail(string calldata _tail) external onlyShedder {
        require(!tailConfigured, "tail already configured");
        tail = _tail;
        tailConfigured = true;
    }

    function deposit() external payable {
        require(msg.value > 0, "value=0");
        balances[msg.sender] += msg.value;
        emit Deposit(msg.sender, msg.value);
    }

    // Deliberately vulnerable: external call happens before state update and uses stale balance snapshot.&#79;&#117;&#114;&#111;&#98;&#111;&#114;&#111;&#115;
    function withdraw(uint256 amount) external {
        uint256 cached = balances[msg.sender];
        require(amount > 0, "amount=0");
        require(cached >= amount, "insufficient");

        if (insideWithdraw && msg.sender == currentCycler) {
            loopDepth[msg.sender] += 1;
            emit Loop(msg.sender, loopDepth[msg.sender], address(this).balance);

            if (!tailUnlocked[msg.sender] && loopDepth[msg.sender] >= 2) {
                tailUnlocked[msg.sender] = true;
                emit TailUnlockedFor(msg.sender, loopDepth[msg.sender]);
            }
        }

        insideWithdraw = true;
        currentCycler = msg.sender;

        (bool ok, ) = msg.sender.call{value: amount}("");
        require(ok, "send failed");

        balances[msg.sender] = cached - amount;

        insideWithdraw = false;
        currentCycler = address(0);
    }

    function revealSecondHalf() external {
        require(tailConfigured, "tail not configured");
        require(tailUnlocked[msg.sender], "bite your tail first");
        emit TailRevealed(msg.sender, tail);
    }

    function verifyFirstHalf(string calldata guess) external view returns (bool) {
        return keccak256(bytes(guess)) == firstHalfCommitment;
    }

    function ouroboricEcho(uint256 depth) external pure returns (bytes32) {
        return _echo(depth);
    }

    function _echo(uint256 depth) internal pure returns (bytes32) {
        if (depth == 0) {
            return keccak256("ouroboros");
        }
        return keccak256(abi.encodePacked(_echo(depth - 1), depth));
    }
}
