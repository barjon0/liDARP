from typing import List, Set, Dict

from main.plan.Planner import Planner
from utils.demand.Request import Request
from utils.helper.EventGraph import EventGraph
from utils.helper.LineGraph import LineGraph
from utils.network.Bus import Bus
from utils.network.Stop import Stop
from utils.plan.Route import Route


class EventBasedMILP(Planner):
    def __init__(self, bus_list: List[Bus], network_graph: LineGraph):
        super().__init__(bus_list, network_graph)
        self.event_graph: EventGraph

    def make_plan(self, new_requests: Set[Request], curr_bus_locations: Dict[Bus, Stop],
                  user_bus_dict: Dict[Request, Bus], user_locations: Dict[Request, Stop], bus_delay: Dict[Bus, float]):
        pass
