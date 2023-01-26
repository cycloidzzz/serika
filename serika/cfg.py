from form_blocks import form_blocks
from utils import (flatten, fresh)

from collections import OrderedDict

import json
import sys


def block_map(block_list):
    num_allocated_block: int = 0

    named_block = OrderedDict()
    for block in block_list:
        if 'label' in block[0]:
            name: str = block[0]['label']
            named_block[name] = block[1:]
        else:
            # an anonymous block, name it
            num_allocated_block += 1
            name: str = f"block{num_allocated_block}"
            named_block[name] = block

    return named_block


def add_terminators(blocks):
    """Given an ordered block map, modify the blocks to add terminators
    to all blocks (avoiding "fall-through" control flow transfers).
    """
    for i, block in enumerate(blocks.values()):
        if not block:
            if i == len(blocks) - 1:
                # In the last block, return.
                block.append({'op': 'ret', 'args': []})
            else:
                dest = list(blocks.keys())[i + 1]
                block.append({'op': 'jmp', 'labels': [dest]})
        elif block[-1]['op'] not in ['br', 'jmp', 'ret']:
            if i == len(blocks) - 1:
                block.append({'op': 'ret', 'args': []})
            else:
                # Otherwise, jump to the next block.
                dest = list(blocks.keys())[i + 1]
                block.append({'op': 'jmp', 'labels': [dest]})


def add_entry(blocks):
    """Ensure that a CFG has a unique entry block with no predecessors.
    If the first block already has no in-edges, do nothing. Otherwise,
    add a new block before it that has no in-edges but transfers control
    to the old first block.
    """
    first_lbl = next(iter(blocks.keys()))

    # Check for any references to the label.
    for instr in flatten(blocks.values()):
        if 'labels' in instr and first_lbl in instr['labels']:
            break
    else:
        return

    # References exist; insert a new block.
    new_lbl = fresh('entry', blocks)
    blocks[new_lbl] = []
    blocks.move_to_end(new_lbl, last=False)


def successors(instr):
    """Get the list of jump target labels for an instruction.
    Raises a ValueError if the instruction is not a terminator (jump,
    branch, or return).
    """
    if instr['op'] in ('jmp', 'br'):
        return instr['labels']
    elif instr['op'] == 'ret':
        return []  # No successors to an exit block.
    else:
        raise ValueError('{} is not a terminator'.format(instr['op']))


def edges(blocks):
    """Given a block map containing blocks complete with terminators,
    generate two mappings: predecessors and successors. Both map block
    names to lists of block names.
    """
    preds = {name: [] for name in blocks}
    succs = {name: [] for name in blocks}
    for name, block in blocks.items():
        for succ in successors(block[-1]):
            succs[name].append(succ)
            preds[succ].append(name)
    return preds, succs


def reassemble(blocks):
    """Flatten a CFG into an instruction list."""
    # This could optimize slightly by opportunistically eliminating
    # `jmp .next` and `ret` terminators where it is allowed.
    instrs = []
    for name, block in blocks.items():
        instrs.append({'label': name})
        instrs += block
    return instrs
