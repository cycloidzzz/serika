from typing import List, Set
import json
import sys
import itertools

from bril_type import JsonType
from form_blocks import form_blocks

# Implementation of local analysis & optimization
# i.e. which happens within the scope of each basic block,
# which can avoids the complex control/data flow analysis.

# TODO (cycloidzzz) : type hints
def trivial_dce_pass(function: JsonType) -> bool:
    """Run a single Dead Code Elimination on the single basic block."""
    blocks = list(form_blocks(function['instrs']))

    changed: bool = False

    used_set: Set[str] = set()
    for block in blocks:
        for inst in block:
            used_set.update(inst.get('args', []))

    for block in blocks:
        new_block = [
            i for i in block if 'dest' not in i or i['dest'] in used_set
        ]
        changed |= (len(block) != len(new_block))
        block[:] = new_block
        print(f"Current block = {block}")

    function['instrs'] = list(itertools.chain(*blocks))
    return changed


def trivial_dce(function: JsonType):
    """Run `trivial_dce_pass` on `function` until convergent"""
    while trivial_dce_pass(function):
        continue


def remove_killed_instructions_pass(function: JsonType):
    blocks = list(form_blocks(function['instrs']))
    changed: bool = False

    for block in blocks:
        last_def_map = {}

        for instr in block:
            # Check for uses of instr
            if 'args' in instr:
                for arg in instr['args']:
                    if arg in last_def_map:
                        del last_def_map[arg]

            # Check for def
            if 'dest' in instr:
                dest: str = instr['dest']
                if dest in last_def_map:
                    changed = True
                    block.remove(last_def_map[dest])
                last_def_map[dest] = instr

    function['instrs'] = list(itertools.chain(*blocks))
    return changed


def trivial_dce_function(func):
    while trivial_dce_pass(func) or remove_killed_instructions_pass(func):
        continue


_LOCAL_DCE_FACTORY = {
    'trivial_dce': trivial_dce,
    'tdce_drop_killed': trivial_dce_function
}


def local_optimization():
    module = json.load(sys.stdin)
    for function in module['functions']:
        print(
            f"function name = {function['name']}, function instr = {function['instrs']}"
        )
        trivial_dce_function(function)
        print(f"functions instrs = {function['instrs']}")


if __name__ == "__main__":
    local_optimization()
