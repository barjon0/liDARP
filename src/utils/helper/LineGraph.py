from typing import List, Set, Dict, Tuple

from utils.helper import Helper
from utils.network import Stop
from utils.network.Bus import Bus
from utils.network.Line import Line


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
    def __init__(self, v1: Stop, v2: Stop, lines: Set[Line], duration: float = -1):
        self.v1 = v1
        self.v2 = v2
        self.lines = lines
        if duration == -1:
            self.duration = Helper.calc_time(Helper.calc_distance(v1, v2))
        else:
            self.duration = duration

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


def make_agg_edges(line_set: Set[Line]):

    # find all transfer points of certain line
    result: List[LineEdge] = []
    for line_a in line_set:
        transfer_stops_a: Set[Stop] = set()
        for line_b in (line_set - {line_a}):
            transfer_stops_a |= (set(line_a.stops) & set(line_b.stops))

        # make lineEdge for all pairs of a line
        for transfer_a in transfer_stops_a:
            for transfer_b in (transfer_stops_a - {transfer_a}):
                duration: float = Helper.calc_time_multi(transfer_a, transfer_b, line_a)
                result.append(LineEdge(transfer_a, transfer_b, {line_a}, duration))

    return result


class LineGraph:
    def __init__(self, network: List[Bus]):
        nodes: Set[Stop] = get_nodes(network)
        self.all_lines: Set[Line] = {bus.line for bus in network}
        self.edges: List[LineEdge] = get_edges(self.all_lines)

        self._graph_dict: Dict[Stop, List[LineEdge]] = {}
        for node in nodes:
            self._graph_dict[node] = []

        for edge in self.edges:
            self._graph_dict[edge.v1].append(edge)
            self._graph_dict[edge.v2].append(edge)

        # find and store all sub-routes between transfer points
        self.aggregated_edges: List[LineEdge] = make_agg_edges(self.all_lines)

    def get_nodes(self):
        return self._graph_dict.keys()

    def get_edges(self):
        return self.edges

    def get_edges_of_node(self, node: Stop):
        return self._graph_dict[node]
