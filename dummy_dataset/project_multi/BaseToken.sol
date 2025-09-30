// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

abstract contract BaseToken {
    string public name;
    string public symbol;
    uint8 public immutable decimals;

    mapping(address => uint256) internal _balances;
    uint256 internal _totalSupply;

    event Transfer(address indexed from, address indexed to, uint256 value);

    constructor(string memory tokenName, string memory tokenSymbol, uint8 tokenDecimals) {
        name = tokenName;
        symbol = tokenSymbol;
        decimals = tokenDecimals;
    }

    function totalSupply() public view returns (uint256) {
        return _totalSupply;
    }

    function balanceOf(address account) public view returns (uint256) {
        return _balances[account];
    }

    function _transfer(address from, address to, uint256 amount) internal {
        require(to != address(0), "BaseToken: zero address");
        uint256 fromBalance = _balances[from];
        require(fromBalance >= amount, "BaseToken: insufficient balance");
        unchecked {
            _balances[from] = fromBalance - amount;
        }
        _balances[to] += amount;
        emit Transfer(from, to, amount);
    }

    function _mint(address account, uint256 amount) internal {
        require(account != address(0), "BaseToken: mint to zero");
        _totalSupply += amount;
        _balances[account] += amount;
        emit Transfer(address(0), account, amount);
    }
}
