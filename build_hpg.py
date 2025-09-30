#!/usr/bin/env python3
"""Build a Heterogeneous Program Graph (HPG) for a Solidity project.

This script loads a Solidity project using Slither, extracts contracts, functions,
and statement-level information, and emits a torch_geometric.data.HeteroData graph
containing structure, control-flow, data-flow, and call relationships.

The resulting graph is persisted to ``project_hpg.pt`` in the current working
directory.
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import torch
from torch_geometric.data import HeteroData

from slither.core.cfg.node import Node, NodeType
from slither.core.declarations.contract import Contract
from slither.core.declarations.function import Function
from slither.slither import Slither

Edge = Tuple[int, int]


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Construct a Heterogeneous Program Graph (HPG) from a Solidity project."
    )
    parser.add_argument(
        "project_path",
        type=str,
        help="Path to the root directory of the Solidity project.",
    )
    return parser.parse_args(argv)


def ensure_directory(path: str) -> None:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Project path does not exist: {path}")
    if not os.path.isdir(path):
        raise NotADirectoryError(f"Project path must be a directory: {path}")


def assign_id(mapping: Dict[object, int], item: object) -> int:
    if item not in mapping:
        mapping[item] = len(mapping)
    return mapping[item]


def is_high_level_call(node: Node) -> bool:
    if hasattr(node, "is_high_level_call"):
        attr = getattr(node, "is_high_level_call")
        if callable(attr):
            try:
                return bool(attr())
            except Exception:
                return False
        return bool(attr)
    return node.type == NodeType.HIGH_LEVEL_CALL


def iter_called_functions(node: Node) -> Iterable[Function]:
    seen = set()
    candidates: List[Function] = []

    for attr_name in ("functions_called", "function_called"):
        if hasattr(node, attr_name):
            attr = getattr(node, attr_name)
            if attr is None:
                continue
            if isinstance(attr, (list, tuple, set)):
                candidates.extend(attr)
            else:
                candidates.append(attr)

    if hasattr(node, "expression"):
        expr = getattr(node, "expression")
        for attr_name in ("function", "function_called", "functions_called"):
            if hasattr(expr, attr_name):
                attr = getattr(expr, attr_name)
                if isinstance(attr, (list, tuple, set)):
                    candidates.extend(attr)
                elif attr is not None:
                    candidates.append(attr)

    for candidate in candidates:
        if isinstance(candidate, Function) and candidate not in seen:
            seen.add(candidate)
            yield candidate


def gather_contracts_and_functions(
    slither: Slither,
    contract_to_id: Dict[Contract, int],
    function_to_id: Dict[Function, int],
    contract_contains_function: List[Edge],
    contract_inherits_contract: List[Edge],
) -> None:
    for contract in slither.contracts:
        contract_id = assign_id(contract_to_id, contract)

        for function in contract.functions_declared + contract.modifiers_declared:
            function_id = assign_id(function_to_id, function)
            contract_contains_function.append((contract_id, function_id))

        for inherited in contract.inheritance:
            if inherited is contract:
                continue
            inherited_id = assign_id(contract_to_id, inherited)
            contract_inherits_contract.append((contract_id, inherited_id))


def gather_statements_and_flows(
    functions: Iterable[Function],
    function_to_id: Dict[Function, int],
    statement_to_id: Dict[Node, int],
    function_contains_statement: List[Edge],
    cfg_edges: List[Edge],
    dfg_edges: List[Edge],
) -> List[Node]:
    all_statement_nodes: List[Node] = []

    for function in functions:
        ordered_nodes = sorted(function.nodes, key=lambda n: n.node_id)
        last_definition: Dict[object, int] = {}

        for node in ordered_nodes:
            statement_id = assign_id(statement_to_id, node)
            function_id = function_to_id[function]
            function_contains_statement.append((function_id, statement_id))
            all_statement_nodes.append(node)

            for successor in node.sons:
                successor_id = assign_id(statement_to_id, successor)
                cfg_edges.append((statement_id, successor_id))

            for variable in getattr(node, "variables_read", []):
                defining_statement = last_definition.get(variable)
                if defining_statement is not None:
                    dfg_edges.append((defining_statement, statement_id))

            for variable in getattr(node, "variables_written", []):
                last_definition[variable] = statement_id

    return all_statement_nodes


def gather_call_edges(
    statement_nodes: Iterable[Node],
    statement_to_id: Dict[Node, int],
    function_to_id: Dict[Function, int],
    call_edges: List[Edge],
) -> None:
    for node in statement_nodes:
        if not is_high_level_call(node):
            continue
        statement_id = statement_to_id[node]
        for function in iter_called_functions(node):
            if function in function_to_id:
                call_edges.append((statement_id, function_to_id[function]))


def to_edge_index(edges: Sequence[Edge]) -> torch.Tensor:
    if not edges:
        return torch.empty((2, 0), dtype=torch.long)
    unique_edges = sorted(set(edges))
    src, dst = zip(*unique_edges)
    return torch.tensor([src, dst], dtype=torch.long)


def identity_features(num_nodes: int) -> torch.Tensor:
    if num_nodes <= 0:
        return torch.empty((0, 0), dtype=torch.float)
    return torch.eye(num_nodes, dtype=torch.float)


def build_hpg(slither: Slither) -> HeteroData:
    contract_to_id: Dict[Contract, int] = {}
    function_to_id: Dict[Function, int] = {}
    statement_to_id: Dict[Node, int] = {}

    contract_contains_function: List[Edge] = []
    contract_inherits_contract: List[Edge] = []
    function_contains_statement: List[Edge] = []
    cfg_edges: List[Edge] = []
    dfg_edges: List[Edge] = []
    call_edges: List[Edge] = []

    gather_contracts_and_functions(
        slither,
        contract_to_id,
        function_to_id,
        contract_contains_function,
        contract_inherits_contract,
    )

    all_statement_nodes = gather_statements_and_flows(
        function_to_id.keys(),
        function_to_id,
        statement_to_id,
        function_contains_statement,
        cfg_edges,
        dfg_edges,
    )

    gather_call_edges(all_statement_nodes, statement_to_id, function_to_id, call_edges)

    hpg = HeteroData()

    hpg["contract"].x = identity_features(len(contract_to_id))
    hpg["function"].x = identity_features(len(function_to_id))
    hpg["statement"].x = identity_features(len(statement_to_id))

    hpg["contract", "contains", "function"].edge_index = to_edge_index(
        contract_contains_function
    )
    hpg["contract", "inherits_from", "contract"].edge_index = to_edge_index(
        contract_inherits_contract
    )
    hpg["function", "contains", "statement"].edge_index = to_edge_index(
        function_contains_statement
    )
    hpg["statement", "cfg_next", "statement"].edge_index = to_edge_index(cfg_edges)
    hpg["statement", "dfg_reaches", "statement"].edge_index = to_edge_index(dfg_edges)
    hpg["statement", "calls", "function"].edge_index = to_edge_index(call_edges)

    return hpg


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    project_path = os.path.abspath(args.project_path)

    try:
        ensure_directory(project_path)
    except (FileNotFoundError, NotADirectoryError) as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 1

    try:
        slither = Slither(project_path)
    except Exception as exc:  # pragma: no cover - slither errors are external
        print(f"[error] Failed to initialize Slither: {exc}", file=sys.stderr)
        return 1

    hpg = build_hpg(slither)
    output_path = os.path.join(os.getcwd(), "project_hpg.pt")
    torch.save(hpg, output_path)
    print(f"Saved HPG to {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
