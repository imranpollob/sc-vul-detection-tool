// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

library TokenUtils {
    error InvalidAmount();

    function revertIfZero(uint256 amount) internal pure {
        if (amount == 0) {
            revert InvalidAmount();
        }
    }
}
