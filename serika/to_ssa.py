import json
import sys
from copy import deepcopy
from collections import defaultdict
from typing import (Dict, List, Optional, Set, Tuple)

from bril_type import (BlockType, JsonType)
from cfg import (block_map, add_entry, add_terminators, edges, reassemble)
from dom import (dominator_tree, dominator_frontier)
from form_blocks import form_blocks


def resolve_defs(func: JsonType, named_block: Dict[str, List[BlockType]]):
    defs: Dict[str, Set[str]] = defaultdict(set)
    # Add defs for function arguments
    entry_block = list(named_block.keys())[0]

    defs.update({arg: entry_block for arg in func.get('args', [])})

    # Add defs for non args
    for name, block in named_block.items():
        for instr in block:
            if 'dest' in instr:
                defs[instr['dest']].add(name)
    return dict(defs)


def resolve_types(func: JsonType):
    """Resolve the type of each variable in `func`"""
    type_map: Dict[str, str] = {}

    # variable type from function args declaration
    type_map.update({arg['name']: arg['type'] for arg in func.get('args', [])})

    # variable type from instr
    for instr in func['instrs']:
        if 'dest' in instr:
            type_map[instr['dest']] = instr['type']
    return type_map


def get_phis(
    named_blocks: Dict[str, BlockType], defs_map: Dict[str, Set[str]],
    dom_front: Dict[str, List[str]]
) -> Dict[str, Set[str]]:
    """Figure out the phis to insert for each basic block."""
    variables: List[str] = list(defs_map.keys())
    block_phis: Dict[str,
                     Set[str]] = {name: set()
                                  for name in named_blocks.keys()}
    for v in variables:
        v_defs: List[str] = list(defs_map[v])
        for name in v_defs:
            for front in dom_front[name]:
                # Insert a phi into the dominator frontier of `block`
                block_phis[front].add(v)
                if front not in defs_map[v]:
                    defs_map[v].add(front)
    return block_phis


def ssa_rename(
    named_blocks: Dict[str, BlockType], func_args: Set[str],
    block_phis: Dict[str, Set[str]], dom_tree: Dict[str, List[str]]
):
    """Rename the variables in the program."""
    var_stack: Dict[str, List[str]] = defaultdict(list)
    counter: Dict[str, int] = defaultdict(int)

    phi_args: Dict[str, Dict[str, Set[Tuple[str, str]]]] = {
        name: {v: set()
               for v in list(v_set)}
        for name, v_set in block_phis.items()
    }
    phi_dest: Dict[str, Dict[str, Optional[str]]] = {
        name: {v: None
               for v in list(v_set)}
        for name, v_set in block_phis.items()
    }

    var_stack.update({v: [v] for v in func_args})

    _, succs = edges(named_blocks)

    def _push_fresh(var: str) -> str:
        fresh_var: str = f"{var}.{counter[var]}"
        counter[var] += 1
        var_stack[var].insert(0, fresh_var)
        return fresh_var

    def _rename(root: str):
        block = named_blocks[root]
        # Save old `var_stack` before push new variables
        old_stack = deepcopy(var_stack)

        # get new variable names for each phi instruction
        for var in block_phis[root]:
            phi_dest[root][var] = _push_fresh(var)

        for instr in block:
            # replace all arguments with the variable name on top of the stack
            if 'args' in instr:
                renamed_args = [var_stack[arg][0] for arg in instr['args']]
                instr['args'] = renamed_args
            # push a new name for current definition
            if 'dest' in instr:
                instr['dest'] = _push_fresh(instr['dest'])

        for succ in succs[root]:
            for phi in block_phis[succ]:
                if phi in var_stack:
                    phi_args[succ][phi].add((root, var_stack[phi][0]))

        for v in dom_tree[root]:
            _rename(v)

        # Resume `var_stack` from saved `old_stack`
        var_stack.clear()
        var_stack.update(old_stack)

    entry: str = list(named_blocks.keys())[0]
    _rename(entry)
    return phi_args, phi_dest


def insert_phis(
    named_blocks: Dict[str, BlockType],
    phi_args: Dict[str, str], phi_dest: Dict[str, Dict[str, str]],
    types_map: Dict[str, str]
) -> None:
    """Insert phis into each basic block."""
    for name, block in named_blocks.items():
        for var, p in phi_dest[name].items():
            arg_pairs: List[Tuple[str, str]] = list(phi_args[name][var])
            if len(arg_pairs) >= 2:
                phi_instr: JsonType = {
                    "op": 'phi',
                    "dest": p,
                    "type": types_map[var],
                    "labels": [arg_pair[0] for arg_pair in arg_pairs],
                    "args": [arg_pair[1] for arg_pair in arg_pairs],
                }
                block.insert(0, phi_instr)


def to_ssa_on_function(func: JsonType):
    named_blocks = block_map(list(form_blocks(func['instrs'])))
    add_entry(named_blocks)
    add_terminators(named_blocks)

    func_args: Set[str] = set([arg for arg in func.get('args', [])])

    def_map: Dict[str, List[str]] = resolve_defs(func, named_blocks)
    types_map: Dict[str, str] = resolve_types(func)

    dom_tree = dominator_tree(named_blocks)
    dom_front = dominator_frontier(named_blocks, dom_tree)

    block_phis = get_phis(named_blocks, def_map, dom_front)

    phi_args, phi_dest = ssa_rename(
        named_blocks, func_args, block_phis, dom_tree
    )

    insert_phis(named_blocks, phi_args, phi_dest, types_map)
    func['instrs'] = reassemble(named_blocks)


def main():
    bril_program: JsonType = json.load(sys.stdin)
    for func in bril_program['functions']:
        to_ssa_on_function(func)
    print(json.dumps(bril_program, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
