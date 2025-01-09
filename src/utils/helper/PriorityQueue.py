import math
from typing import List, Dict

from utils.network.Stop import Stop


class PriorityQueue:
    def __init__(self, nodes: List[Stop]):
        self.node_dict: Dict[Stop, float] = {}
        self.priority_dict: Dict[float, List[Stop]] = {math.inf: []}
        self.final_vals: Dict[Stop, float] = {}

        for node in nodes:
            self.node_dict[node] = math.inf
            self.priority_dict[math.inf].append(node)

    def pop(self):
        priorities = self.priority_dict.keys()
        min_value: float = min(priorities)
        poss_nodes = self.priority_dict.get(min_value)
        node: Stop = poss_nodes[0]

        if len(poss_nodes) > 1:
            poss_nodes.remove(node)
        else:
            self.priority_dict.pop(min_value)

        self.final_vals[node] = self.node_dict.pop(node)

        return node, min_value

    def replace(self, node: Stop, new_priority: float):
        old_val = self.node_dict[node]
        self.node_dict[node] = new_priority

        old_list = self.priority_dict[old_val]
        old_list.remove(node)
        if len(old_list) == 0:
            self.priority_dict.pop(old_val)

        if new_priority in self.priority_dict:
            self.priority_dict[new_priority].append(node)
        else:
            self.priority_dict[new_priority] = [node]

    def get_priority(self, node: Stop):
        return self.node_dict.get(node)

    def is_empty(self):
        if len(self.node_dict.keys()) > 0:
            return False
        else:
            return True
