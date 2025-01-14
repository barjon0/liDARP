import math
from typing import List, Dict, TypeVar, Generic

T = TypeVar('T')


class PriorityQueue(Generic[T]):
    def __init__(self, nodes: List[T]):
        self.node_dict: Dict[T, float] = {}
        self.priority_dict: Dict[float, List[T]] = {math.inf: []}
        self.final_vals: Dict[T, float] = {}

        for node in nodes:
            self.node_dict[node] = math.inf
            self.priority_dict[math.inf].append(node)

    def pop(self):
        priorities = self.priority_dict.keys()
        min_value: float = min(priorities)
        poss_nodes = self.priority_dict.get(min_value)
        node: T = poss_nodes[0]

        if len(poss_nodes) > 1:
            poss_nodes.remove(node)
        else:
            self.priority_dict.pop(min_value)

        try:
            self.final_vals[node] = self.node_dict.pop(node)
        except KeyError:
            print(node[0].id)

        return node, min_value

    def add_node(self, node: T, priority: float):
        self.node_dict[node] = priority
        if priority in self.priority_dict:
            self.priority_dict[priority].append(node)
        else:
            self.priority_dict[priority] = [node]

    def replace(self, node: T, new_priority: float):
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

    def get_priority(self, node: T):
        if node in self.final_vals:  # if node was already finished -> return none
            return None
        elif node in self.node_dict:  # if node still there return value
            return self.node_dict[node]
        else:
            self.add_node(node, math.inf)  # if node new -> add to queue and return infinity
            return math.inf

    def is_empty(self):
        if len(self.node_dict.keys()) > 0:
            return False
        else:
            return True
