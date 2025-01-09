from typing import List

from utils.helper.EventGraph import EventGraph
from utils.network.Bus import Bus
from utils.plan.Route import Route


class EventBasedMILP:
    def __init__(self, network: List[Bus]):
        self.network = network
        self.planned_routes: List[Route] = []
        self.event_graph: EventGraph
