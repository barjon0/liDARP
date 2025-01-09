from typing import List, Set, Dict

from utils.helper import Helper
from utils.network.Bus import Bus
from utils.network.Line import Line
from utils.network.Stop import Stop


# edges between two stops: contain lines travelling there and duration of travel
# make edge class containing these things -> store as list of edges and nodes

def get_nodes(network):
    node_set: Set[Stop] = set()
    for bus in network:
        for stop in bus.line.stops:
            node_set.add(stop)
    return node_set


def get_edges(all_lines: Set[Line]):
    found_edges: List[LineEdge] = []
    for line in all_lines:
        for i in range(1, len(line.stops)):
            found_edges.append(LineEdge(line.stops[i - 1], line.stops[i], {line}))

    hash_dict: Dict[int, List[LineEdge]] = {}
    for edge in found_edges:
        if hash(edge) not in hash_dict:
            hash_dict[hash(edge)] = [edge]
        else:
            hash_dict[hash(edge)].append(edge)

    final_edges: List[LineEdge] = []
    for key in hash_dict.keys():
        same_edges = hash_dict[key]
        single_edge = same_edges[0]
        for i in range(1, len(same_edges)):
            single_edge.lines += same_edges[i].lines
        final_edges.append(single_edge)

    return final_edges


class LineEdge:
    def __init__(self, v1: Stop, v2: Stop, lines: Set[Line]):
        self.v1 = v1
        self.v2 = v2
        self.lines = lines
        self.duration = Helper.calc_time(Helper.calc_distance(v1, v2))

    def contains_stop(self, v: Stop):
        if self.v1 == v or self.v2 == v:
            return True
        else:
            return False

    def get_neighbour(self, v: Stop):
        if self.v1 == v:
            return self.v2
        elif self.v2 == v:
            return self.v1
        else:
            ValueError("edge accessed with node not part of it")

    def __eq__(self, other):
        other_edge: LineEdge = other
        if self.v1 == other_edge.v1 or self.v1 == other_edge.v2:
            if self.v2 == other_edge.v2 or self.v2 == other_edge.v1:
                return True
        return False

    def __hash__(self):
        # hash only depends on nodes, no matter the order
        return hash(frozenset({self.v1, self.v2}))


class LineGraph:
    def __init__(self, network: List[Bus]):
        nodes: Set[Stop] = get_nodes(network)
        all_lines: Set[Line] = {bus.line for bus in network}
        self.edges: List[LineEdge] = get_edges(all_lines)

        self._graph_dict: Dict[Stop, List[LineEdge]] = {}
        for node in nodes:
            self._graph_dict[node] = []

        for edge in self.edges:
            self._graph_dict[edge.v1].append(edge)
            self._graph_dict[edge.v2].append(edge)

    def get_nodes(self):
        return self._graph_dict.keys()

    def get_edges(self):
        return self.edges

    def get_edges_of_node(self, node: Stop):
        return self._graph_dict[node]
