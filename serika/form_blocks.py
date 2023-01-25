from typing import Dict, Iterable, List, Tuple

BRANCH_INSTS: List[str] = ['br', 'jmp', 'ret']


def form_blocks(instructions: List):
    # The basic block should start with labels and end with control flow instructions
    # like ['br', 'jmp', 'ret']

    cur_block = []
    for inst in instructions:
        # TODO (cycloidzzz): assert that label only appears at the start of each basic block.
        if 'op' not in inst:
            # a label
            cur_block.append(inst)
        else:
            # an instruction
            if inst['op'] in BRANCH_INSTS:
                cur_block.append(inst)
                yield cur_block
                cur_block = []
            else:
                cur_block.append(inst)
    yield cur_block
