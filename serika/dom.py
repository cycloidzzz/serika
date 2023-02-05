from cfg import (block_map, add_entry, add_terminators, successors, edges)
from form_blocks import form_blocks

import json
import sys

from collections import defaultdict, OrderedDict
from typing import Dict, List, Set, Tuple


def dfs(named_blocks) -> Tuple[Dict[str, int], Dict[int, str], Dict[str, str]]:
    predecessors, successors = edges(named_blocks)

    dfn_num = 0
    dfn_map: Dict[str, int] = {}
    parent: Dict[str, str] = {}
    dfn_to_block: Dict[int, str] = {}

    def _dfs_handler(v: str):
        if v not in dfn_map:
            nonlocal dfn_num
            dfn_num += 1
            dfn_map[v] = dfn_num
            dfn_to_block[dfn_num] = v

        for vertex in successors[v]:
            if vertex not in dfn_map:
                parent[vertex] = v
                _dfs_handler(vertex)

    root: str = list(named_blocks.keys())[0]

    _dfs_handler(root)

    return dfn_map, dfn_to_block, parent


# Solve immediate dominator with Lengauer-Tarjan Algorithm
def dominator_tree(named_blocks) -> Dict[str, List[str]]:

    predecessors, successors = edges(named_blocks)

    dfn, dfn_to_block, parent = dfs(named_blocks)

    semi: Dict[str, str] = {}
    ancestor: Dict[str, str] = {}
    best: Dict[str, str] = {}
    bucket: Dict[str, List[str]] = defaultdict(lambda: [])

    idom: Dict[str, str] = {}
    rdom: Dict[str, str] = {}

    idom_inv: Dict[str, List[str]] = OrderedDict(
        {name: []
         for name, _ in named_blocks.items()}
    )

    def _eval(v: str):
        a: str = ancestor[v]
        if a in ancestor and ancestor[a] in ancestor:
            b = _eval(ancestor[a])
            if dfn[semi[b]] < dfn[semi[v]]:
                best[v] = b
            ancestor[v] = ancestor[a]
        return best[v]

    for i in range(len(named_blocks), 1, -1):
        v = dfn_to_block[i]
        p = parent[v]

        s = parent[v]
        for pred in predecessors[v]:
            if dfn[pred] <= dfn[v]:
                temp = pred
            else:
                temp = semi[_eval(pred)]
            if dfn[s] > dfn[temp]:
                s = temp

        # The semi dominator of v is s
        semi[v] = s
        bucket[s].append(v)

        ancestor[v] = p
        best[v] = v

        for vertex in bucket[p]:
            b = _eval(vertex)
            if semi[b] == semi[vertex]:
                idom[vertex] = semi[vertex]
            else:
                rdom[vertex] = b
        bucket[p].clear()

    for i in range(2, len(named_blocks) + 1):
        v = dfn_to_block[i]
        if v not in idom:
            idom[v] = idom[rdom[v]]
        idom_inv[idom[v]].append(v)

    return idom_inv


def postorder_traverse(root, succ):
    def _postorder_helper(root: str, visited: Set[str], result):
        if root in visited:
            return
        visited.add(root)

        for s in succ[root]:
            _postorder_helper(s, visited, result)
        result.append(root)

    result: List[str] = []
    _postorder_helper(root, set(), result)

    return result


# FIXME(cycloidzzz): this implementation might be very slow if dom_tree[v] is a list ...
def dominator_frontier(named_blocks, dom_tree):
    # NOTE: Actually we are calculating the dominator frontier
    # with the help of dominance-join graph (a.k.a. DJ-Graph)
    _, succs = edges(named_blocks)

    root = list(named_blocks.keys())[0]
    postorder_list = postorder_traverse(root, dom_tree)

    fronts: Dict[str, List[str]] = OrderedDict()

    for v in postorder_list:
        temp_fronts: Set[str] = set()

        temp_fronts.update([y for y in succs[v] if y not in dom_tree[v]])

        for z in dom_tree[v]:
            temp_fronts.update([y for y in fronts[z] if y not in dom_tree[v]])

        fronts[v] = list(temp_fronts)

    return fronts


def print_idom():
    module = json.load(sys.stdin)
    for function in module['functions']:
        print(f"function name = {function['name']}")
        named_blocks = block_map(form_blocks(function['instrs']))
        add_entry(named_blocks)
        add_terminators(named_blocks)

        dom_tree = dominator_tree(named_blocks)
        print(dom_tree)

        dom_front = dominator_frontier(named_blocks, dom_tree)
        print(dom_front)


if __name__ == "__main__":
    print_idom()
