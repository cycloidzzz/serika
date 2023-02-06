from typing import Dict, Set, List
from collections import defaultdict

import json
import sys

from bril_type import JsonType
from cfg import (block_map, add_entry, add_terminators, edges)
from form_blocks import form_blocks


# A simple reaching definition anaylsis
def solve_use(block: List[JsonType]) -> Set[str]:
    # get the use set of block
    uses: Set[str] = set()
    defined: Set[str] = set()
    for instr in block:
        if 'op' in instr:
            if 'args' in instr:
                uses.update(
                    [arg for arg in instr['args'] if arg not in defined]
                )
            if 'dest' in instr:
                defined.add(instr['dest'])
    return uses


def solve_def(block: List[JsonType]) -> Set[str]:
    defs: Set[str] = set()
    for instr in block:
        if 'op' in instr:
            if 'dest' in instr:
                defs.add(instr['dest'])
    return defs


def union(facts: List[Set[str]]) -> Set[str]:
    fact_union: Set[str] = set()
    for fact in facts:
        fact_union.update(fact)
    return fact_union


def live_variable_analysis(named_blocks: Dict[str, List[JsonType]]):
    block_def: Dict[str, Set[str]] = {}
    block_use: Dict[str, Set[str]] = {}

    block_in: Dict[str, Set[str]] = defaultdict(lambda: set())
    block_out: Dict[str, Set[str]] = defaultdict(lambda: set())

    # backward
    pred, succ = edges(named_blocks)

    for name, block in named_blocks.items():
        block_def[name] = solve_def(block)
        block_use[name] = solve_use(block)

    while True:
        changed: bool = False

        for name, block in named_blocks.items():
            fact_union = union([block_in[v] for v in succ[name]])
            if len(fact_union ^ block_out[name]) > 0:
                changed = True

            block_out[name] = fact_union
            block_in[name] = (block_out[name] -
                              block_def[name]) | block_use[name]

        if not changed:
            break

    print(block_in)
    print(block_out)


def dataflow_analysis():
    program: JsonType = json.load(sys.stdin)
    for function in program['functions']:
        named_blocks = block_map(list(form_blocks(function['instrs'])))
        add_entry(named_blocks)
        add_terminators(named_blocks)

        # Run iterative dataflow analysis framework
        live_variable_analysis(named_blocks)


if __name__ == "__main__":
    dataflow_analysis()
