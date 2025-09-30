// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "./BaseToken.sol";
import "./TokenUtils.sol";

contract MyToken is BaseToken {
    address public owner;

    modifier onlyOwner() {
        require(msg.sender == owner, "MyToken: not owner");
        _;
    }

    constructor() BaseToken("My Token", "MYT", 18) {
        owner = msg.sender;
        _mint(msg.sender, 1_000_000 ether);
    }

    function transfer(address to, uint256 amount) external returns (bool) {
        TokenUtils.revertIfZero(amount);
        _transfer(msg.sender, to, amount);
        return true;
    }

    function mint(address to, uint256 amount) external onlyOwner {
        _mint(to, amount);
    }
}
