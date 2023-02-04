import itertools


def flatten(blocks):
    return list(itertools.chain(*blocks))


def fresh(seed, names):
    """Generate a new name that is not in `names` starting with `seed`.
    """
    i = 1
    while True:
        name = seed + str(i)
        if name not in names:
            return name
        i += 1

import json
import sys


def is_ssa(bril):
    """Check whether a Bril program is in SSA form.
    Every function in the program may assign to each variable once.
    """
    for func in bril['functions']:
        assigned = set()
        for instr in func['instrs']:
            if 'dest' in instr:
                if instr['dest'] in assigned:
                    return False
                else:
                    assigned.add(instr['dest'])
    return True


if __name__ == '__main__':
    print('yes' if is_ssa(json.load(sys.stdin)) else 'no')