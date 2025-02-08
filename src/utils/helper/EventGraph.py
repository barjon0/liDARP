from typing import List, Set, Tuple, Dict

from utils.demand.SplitRequest import SplitRequest
from utils.network.Line import Line


class Event:
    def __init__(self, first: SplitRequest = None, remaining=None):
        if remaining is None:
            remaining = set()
        self.remaining = {x.id for x in remaining}
        self.first = first

    def set_before_event(self):
        pass

    def set_after_event(self):
        pass


class IdleEvent(Event):
    def __init__(self, line: Line, ):
        super().__init__()
        self.location = line.depot

    def set_before_event(self):
        return frozenset()

    def set_after_event(self):
        return frozenset()


class PickUpEvent(Event):
    def __init__(self, first: SplitRequest, remaining: Set[SplitRequest]):
        self.location = first.pick_up_location
        super().__init__(first, remaining)

    def set_before_event(self):
        return frozenset(self.remaining)

    def set_after_event(self):
        return frozenset(self.remaining | {self.first.id})


class DropOffEvent(Event):
    def __init__(self, first: SplitRequest, remaining: Set[SplitRequest]):
        self.location = first.drop_off_location
        super().__init__(first, remaining)

    def set_before_event(self):
        return frozenset(self.remaining | {self.first.id})

    def set_after_event(self):
        return frozenset(self.remaining)


class EventGraph:
    def __init__(self):
        self._request_dict: Dict[SplitRequest, Tuple[Set[Event], Set[Event]]] = {}
        self.edge_dict: Dict[Event, Tuple[Set[Event], Set[Event]]] = {}

    def get_edges_in(self, event: Event):
        return self.edge_dict[event][0]

    def get_edges_out(self, event: Event):
        return self.edge_dict[event][1]

    # add all events of a single line together, generates edges
    def add_events(self, event_set_line: Set[Event]):
        self.edge_dict |= {x: (set(), set()) for x in event_set_line}
        split_requests = {x.first for x in event_set_line if not isinstance(x, IdleEvent)}
        self._request_dict |= {x: (set(), set()) for x in split_requests}

        hash_dict: Dict[int, Set[Tuple[bool, Event]]] = {}

        for event in event_set_line:
            if isinstance(event, PickUpEvent):
                self._request_dict[event.first][0].add(event)
            elif isinstance(event, DropOffEvent):
                self._request_dict[event.first][1].add(event)

            key_before: int = hash(event.set_before_event())
            key_after: int = hash(event.set_after_event())

            # hopefully hash function does not have collisions
            if key_before in hash_dict:
                hash_dict[key_before].add((True, event))
            else:
                hash_dict[key_before] = {(True, event)}

            if key_after in hash_dict:
                hash_dict[key_after].add((False, event))
            else:
                hash_dict[key_after] = {(False, event)}

        for key in hash_dict:
            same_pass_events_pre = {x[1] for x in hash_dict[key] if x[0]}
            same_pass_events_after = {x[1] for x in hash_dict[key] if not x[0]}

            for event_pre in same_pass_events_pre:
                self.edge_dict[event_pre][0].update({x for x in same_pass_events_after if x != event_pre})

            # comprehension here for filtering out idle pointing to idle
            for event_after in same_pass_events_after:
                self.edge_dict[event_after][1].update({x for x in same_pass_events_pre if x != event_after})
