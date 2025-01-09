from typing import List, Set

from utils.demand.SplitRequest import SplitRequest


class Event:
    def __init__(self, event_type: bool, first: SplitRequest, remaining: Set[SplitRequest]):
        self.remaining = [x.id for x in remaining]
        self.first = first.id
        self.type = event_type
        if event_type:
            self.location = first.drop_off_location
        else:
            self.location = first.pick_up_location


class EventGraph:
    def __init__(self, events: List[Event], edges: List[List[int]]):
        self.edges = edges
        self.events = events
