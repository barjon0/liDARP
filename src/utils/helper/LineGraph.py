from typing import List, Set, Dict, Tuple

from utils.helper import Timer
from utils.network import Stop
from utils.network.Bus import Bus
from utils.network.Line import Line


class LineEdge:
    def __init__(self, v1: Stop, v2: Stop, line: Line, duration: float = -1):
        from utils.helper import Helper
        self.v1 = v1
        self.v2 = v2
        self.line = line
        if duration == -1:
            self.duration = Timer.calc_time(Helper.calc_distance(v1, v2))
        else:
            self.duration = duration

    def contains_stop(self, v: Stop):
        if self.v1 == v or self.v2 == v:
            return True
        else:
            return False


# only aggregated edges of graph, specific for each request(add s -> transfer, transfer -> end, s -> t separately)
# edges are directed, unique for every line and linked to in both directions
# incoming edges are at 0, outgoing at 1
class LineGraph:
    def __init__(self, network: List[Bus]):
        self.all_lines: Set[Line] = {bus.line for bus in network}
        self._graph_dict: Dict[Stop, Tuple[Set[LineEdge], Set[LineEdge]]] = {}
        self._make_graph()

        self.all_stops: Set[Stop] = set().union(*[set(x.stops) for x in self.all_lines])

    def get_nodes(self):
        return self._graph_dict.keys()

    def get_edges(self):
        return set().union(*[x[0] | x[1] for x in self._graph_dict.values()])

    def get_edges_in(self, node: Stop):
        return self._graph_dict[node][0]

    def get_edges_out(self, node: Stop):
        return self._graph_dict[node][1]

    def _make_graph(self):
        from utils.helper import Helper
        # creates basic aggregated edges to be reused
        for line_a in self.all_lines:
            transfer_stops_a: Set[Stop] = set()
            for other_line in (self.all_lines - {line_a}):
                transfer_stops_a |= set(line_a.stops) & set(other_line.stops)

            # make lineEdge for all pairs of a line
            for transfer_a in transfer_stops_a:
                for other_stop in (transfer_stops_a - {transfer_a}):
                    duration: float = Timer.calc_time(Helper.calc_distance(transfer_a, other_stop))
                    edge_to = LineEdge(transfer_a, other_stop, line_a, duration)
                    if transfer_a in self._graph_dict:
                        self._graph_dict[transfer_a][1].add(edge_to)
                    else:
                        self._graph_dict[transfer_a] = (set(), {edge_to})

                    if other_stop in self._graph_dict:
                        self._graph_dict[other_stop][0].add(edge_to)
                    else:
                        self._graph_dict[transfer_a] = ({edge_to}, set())

    def add_request(self, search_pick_up: Stop, search_drop_off: Stop):
        from utils.helper import Helper
        # add request stops to graph

        if search_pick_up not in self._graph_dict:
            pick_up_line = next((x for x in self.all_lines if search_pick_up in x.stops))
            transfer_stops: Set[Stop] = self.get_nodes() & set(pick_up_line.stops)
            self._graph_dict[search_pick_up] = (set(), set())
            for stop in transfer_stops:
                duration: float = Timer.calc_time(Helper.calc_distance(search_pick_up, stop))
                edge_to = LineEdge(search_pick_up, stop, pick_up_line, duration)
                self._graph_dict[search_pick_up][1].add(edge_to)
                self._graph_dict[stop][0].add(edge_to)

        if search_drop_off not in self._graph_dict:
            drop_off_line = next((x for x in self.all_lines if search_drop_off in x.stops))
            transfer_stops: Set[Stop] = self.get_nodes() & set(drop_off_line.stops)
            self._graph_dict[search_drop_off] = (set(), set())
            for stop in transfer_stops:
                duration: float = Timer.calc_time(Helper.calc_distance(stop, search_drop_off))
                edge_from = LineEdge(stop, search_drop_off, drop_off_line, duration)
                self._graph_dict[search_drop_off][0].add(edge_from)
                self._graph_dict[stop][1].add(edge_from)

    def delete_request(self, old_pick_up: Stop, old_drop_off: Stop):
        # delete edges and nodes of old request when finished
        pick_up_lines: Set[Line] = {x for x in self.all_lines if old_pick_up in x.stops}
        drop_off_lines: Set[Line] = {x for x in self.all_lines if old_drop_off in x.stops}

        if len(pick_up_lines) == 1:
            for edge in self._graph_dict[old_pick_up][1]:
                self._graph_dict[edge.v2][0].remove(edge)
            del self._graph_dict[old_pick_up]

        if len(drop_off_lines) == 1:
            for edge in self._graph_dict[old_drop_off][0]:
                self._graph_dict[edge.v1][1].remove(edge)
            del self._graph_dict[old_drop_off]
