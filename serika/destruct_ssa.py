import json
import sys
from typing import (Dict, List, Tuple)

from bril_type import (BlockType, JsonType)
from cfg import (block_map, add_entry, add_terminators, edges, reassemble)
from form_blocks import form_blocks


def run_on_func(named_blocks: Dict[str, BlockType]):
    # For each phi instruction such that a0 <- Phi(a1 b1, a2 b2, a3 b3, ... ak bk),
    # we insert a0 <- aj to the end of basic block bj.
    for instrs in named_blocks.values():
        # Get all phis from instrs
        for instr in instrs:
            if instr.get('op') == 'phi':
                preds: List[str] = instr.get('labels')
                values: List[str] = instr.get('args')
                for (pred, value) in zip(preds, values):
                    named_blocks[pred].insert(
                        -1, {
                            "op": 'id',
                            "dest": instr.get('dest'),
                            "type": instr.get('type'),
                            "args": [value]
                        }
                    )

        filtered_instrs: BlockType = [
            instr for instr in instrs if instr.get('op') != 'phi'
        ]
        instrs[:] = filtered_instrs


def destruct_cssa(func: JsonType):
    """Convert a program out of conventional-SSA form (a.k.a freshly built SSA) """
    named_blocks: Dict[str, BlockType] = block_map(
        list(form_blocks(func['instrs']))
    )
    add_entry(named_blocks)
    add_terminators(named_blocks)

    run_on_func(named_blocks)
    func['instrs'] = reassemble(named_blocks)


# TODO (cycloidzzz): ssa destructor for transformed-SSA
# TODO (cycloidzzz): some optimization based on ssa form, you can check out the SSA book ...


def main():
    bril_program: JsonType = json.load(sys.stdin)
    for func in bril_program['functions']:
        #print(func)
        destruct_cssa(func)
    print(json.dumps(bril_program, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
