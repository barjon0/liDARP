from typing import List, Set, Tuple, Dict

import Global
from utils.demand.SplitRequest import SplitRequest
from utils.helper import Timer, Helper
from utils.helper.Timer import TimeImpl
from utils.network.Line import Line


class Event:
    def __init__(self, first: SplitRequest = None, remaining=None):
        if remaining is None:
            remaining = set()
        self.remaining = {x.id for x in remaining}
        self.first = first
        self.earl_depart = None
        self.lat_depart = None
        self.location = None

    def set_before_event(self):
        pass

    def set_after_event(self):
        pass


class IdleEvent(Event):
    def __init__(self, line: Line):
        super().__init__()
        self.location = line.depot
        self.line = line
        self.earl_depart = TimeImpl(0, 0)
        self.lat_depart = TimeImpl(24, 0)

    def set_before_event(self):
        return frozenset()

    def set_after_event(self):
        return frozenset()

    def __repr__(self):
        return f"IdleEvent(user:-; others:[]; location:{self.location.id}; line:{self.line.id})"


class PickUpEvent(Event):
    def __init__(self, first: SplitRequest, remaining: Set[SplitRequest], earl_time: TimeImpl, lat_time: TimeImpl):
        super().__init__(first, remaining)
        self.location = first.pick_up_location
        self.earl_depart = earl_time
        self.lat_depart = lat_time

    def set_before_event(self):
        return frozenset(self.remaining)

    def set_after_event(self):
        return frozenset(self.remaining | {self.first.id})

    def __repr__(self):
        return f"PickUpEvent(user:{self.first.id}; others:{self.remaining}; location:{self.location.id}; line:{self.first.line.id})"


class DropOffEvent(Event):
    def __init__(self, first: SplitRequest, remaining: Set[SplitRequest], earl_time: TimeImpl, lat_time: TimeImpl):
        super().__init__(first, remaining)
        self.location = first.drop_off_location
        self.earl_depart = earl_time
        self.lat_depart = lat_time

    def set_before_event(self):
        return frozenset(self.remaining | {self.first.id})

    def set_after_event(self):
        return frozenset(self.remaining)

    def __repr__(self):
        return f"DropOffEvent(user:{self.first.id}; others:{self.remaining}; location:{self.location.id}; line:{self.first.line.id})"


class EventGraph:
    def __init__(self):
        self._request_dict: Dict[SplitRequest, Tuple[Set[Event], Set[Event]]] = {}
        self.edge_dict: Dict[Event, Tuple[Set[Event], Set[Event]]] = {}

    def get_edges_in(self, event: Event):
        return self.edge_dict[event][0]

    def get_edges_out(self, event: Event):
        return self.edge_dict[event][1]

    # delete all nodes, that do not have path to and from idle
    def check_connectivity(self, idle_event: IdleEvent):
        look_up_dict: Dict[Event, List[bool, bool]] = {x: [False, False] for x in self.edge_dict.keys() if
                                                       not isinstance(x, IdleEvent) and x.first.line == idle_event.line}
        look_up_dict |= {idle_event: [True, True]}

        # do breadth-search for incoming and outgoing edges, respectively
        # conjunct per idle_event -> delete all others
        found_sets: Tuple[Set[Event], Set[Event]] = ({idle_event}, {idle_event})

        for i in {0, 1}:
            last_found: Set[Event] = {idle_event}
            while len(last_found) > 0:
                new_found = set()
                for event in last_found:
                    for neighbour in self.edge_dict[event][i]:
                        if not look_up_dict[neighbour][i]:
                            new_found.add(neighbour)
                            look_up_dict[neighbour][i] = True
                last_found = new_found
                found_sets[i].update(last_found)

        overall_found = found_sets[0] & found_sets[1]

        unconnected_events = set(look_up_dict.keys()) - overall_found
        if len(unconnected_events) > 0:
            ValueError("There are events in EventGraph not connected to idle event")

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
            same_pass_events_succ: Set[Event] = {x[1] for x in hash_dict[key] if x[0]}
            same_pass_events_pred: Set[Event] = {x[1] for x in hash_dict[key] if not x[0]}

            for event_before in same_pass_events_pred:
                for event_after in same_pass_events_succ:
                    duration = Timer.calc_time(Helper.calc_distance(event_before.location, event_after.location))
                    if (event_before is not event_after) and event_before.earl_depart.add_minutes(
                            duration + Global.TRANSFER_MINUTES) <= event_after.lat_depart:
                        self.edge_dict[event_after][0].add(event_before)
                        self.edge_dict[event_before][1].add(event_after)
