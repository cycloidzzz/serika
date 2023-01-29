from typing import Dict, Iterable, List, Tuple
from bril_type import JsonType

BRANCH_INSTS: List[str] = ['br', 'jmp', 'ret']


def form_blocks(instructions: List[JsonType]) -> Iterable[List[JsonType]]:
    # The basic block should start with labels and end with control flow instructions
    # like ['br', 'jmp', 'ret']

    cur_block = []
    for inst in instructions:
        if 'op' not in inst:
            # a label
            if cur_block:
                # if inst is a label, then must be the beginning of a basic block
                yield cur_block
            cur_block = [inst]
        else:
            # an instruction
            if inst['op'] in BRANCH_INSTS:
                cur_block.append(inst)
                yield cur_block
                cur_block = []
            else:
                cur_block.append(inst)
    yield cur_block
