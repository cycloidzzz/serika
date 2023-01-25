from typing import List, Set
import json
import sys
import itertools

from form_blocks import form_blocks


# TODO (cycloidzzz) : type hints
def simple_dce_pass(function) -> bool:
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


def local_optimization():
    module = json.load(sys.stdin)
    for function in module['functions']:
        print(
            f"function name = {function['name']}, function instr = {function['instrs']}"
        )
        simple_dce_pass(function)
        print(f"functions instrs = {function['instrs']}")


if __name__ == "__main__":
    local_optimization()
