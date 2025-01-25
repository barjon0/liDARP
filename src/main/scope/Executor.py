from datetime import time
from typing import Set, Dict, List

from utils.demand import Request
from utils.helper import Helper
from utils.network.Bus import Bus
from utils.network.Stop import Stop

from utils.plan.Route import Route
from utils.plan.RouteStop import RouteStop


class Executor:
    def __init__(self, busses: List[Bus]):
        self.user_locations: Dict[Request, Stop] = {}  # for waiting users
        self.passengers: Dict[Bus, Set[Request]] = {x: set() for x in busses}
        self.bus_locations: Dict[Bus, Stop] = {x: x.depot for x in
                                               busses}  # locations of bus (or next location bus is arriving at)
        self.bus_delay: Dict[Bus, time] = {x: time(0, 0) for x in busses}  # time of bus to arriving at next stop
        self.routes = [Route(x) for x in busses]

        self.routes.sort(key=lambda x: x.bus.id)

    def check_plan(self, done_r_stops: List[RouteStop], final_time: time = None):

        waiting_bus_events: List[RouteStop] = []
        curr_time: time
        for r_stop in done_r_stops:
            curr_time = r_stop.arriv_time
            self.bus_locations[r_stop.bus] = r_stop.stop

            for u_dropped in r_stop.drop_off:
                if u_dropped not in self.passengers[r_stop.bus]:
                    ValueError("Person not supposed to be in bus")
                else:
                    self.passengers[r_stop.bus].remove(u_dropped)
                if r_stop.stop is not u_dropped.drop_off_location:
                    self.user_locations[u_dropped] = r_stop.stop
                else:
                    u_dropped.act_end_time = r_stop.arriv_time

            for wait_event in waiting_bus_events:
                if wait_event.depart_time <= curr_time:
                    for u_picked in wait_event.pick_up:
                        this_stop = self.user_locations.pop(u_picked)
                        if this_stop is not wait_event.stop:
                            ValueError("Missmatch between expected pick-up stop and actual")
                        self.passengers[wait_event.bus].add(u_picked)
                        if wait_event.stop is u_picked.pick_up_location:
                            u_picked.act_start_time = wait_event.depart_time
                waiting_bus_events.remove(wait_event)

            waiting_bus_events.append(r_stop)

        # for waiting_bus_events change depart_time and empty pick-up set if not finished
        if final_time is not None:
            for wait_event in waiting_bus_events:
                if wait_event.depart_time <= final_time:
                    for u_picked in wait_event.pick_up:
                        this_stop = self.user_locations.pop(u_picked)
                        if this_stop is not wait_event.stop:
                            ValueError("Missmatch between expected pick-up stop and actual")
                        self.passengers[wait_event.bus].add(u_picked)
                        if u_picked.pick_up_location is wait_event.stop:
                            u_picked.act_start_time = wait_event.depart_time
                else:
                    wait_event.depart_time = final_time
                    wait_event.pick_up.clear()
        else:
            for wait_event in waiting_bus_events:
                for u_picked in wait_event.pick_up:
                    this_stop = self.user_locations.pop(u_picked)
                    if this_stop is not wait_event.stop:
                        ValueError("Missmatch between expected pick-up stop and actual")
                    self.passengers[wait_event.bus].add(u_picked)
                    if u_picked.pick_up_location is wait_event.stop:
                        u_picked.act_start_time = wait_event.depart_time

    # could observe everything here make sure there are no inconsistencies
    def execute_plan(self, curr_routes: List[Route], time_next: time):
        # if time_next = none : -> just copy entire plan to result
        # else: look through curr. route until just before time_next -> copy to result -> update dictionaries

        curr_routes.sort(key=lambda x: x.id)
        if time_next is None:
            for route_count in range(len(curr_routes)):
                self.routes[route_count].stop_list += curr_routes[route_count].stop_list

            all_r_stops: List[RouteStop] = []
            for route in curr_routes:
                all_r_stops += route.stop_list

            all_r_stops.sort(key=lambda x: x.arriv_time)
            self.check_plan(all_r_stops)

        else:
            done_r_stops = []
            for route_count in range(len(curr_routes)):
                time_count: time
                if len(curr_routes[route_count].stop_list) > 0:
                    time_count = curr_routes[route_count].stop_list[0].arriv_time
                counter = 0
                while counter < len(curr_routes[route_count].stop_list) and time_count < time_next:
                    done_r_stops.append(curr_routes[route_count].stop_list[counter])
                    self.routes[route_count].stop_list.append(curr_routes[route_count].stop_list[counter])

                    counter += 1
                    time_count = curr_routes[route_count].stop_list[counter].arriv_time

                # could lead to inconsistencies in dynamic case: not finished stop_events are counted as fully processed, but are cut short(pick-ups not done)
                if counter < len(curr_routes[route_count].stop_list):
                    self.bus_delay[curr_routes[route_count].bus] = Helper.sub_times(time_count, time_next)

            done_r_stops.sort(key=lambda x: x.arriv_time)
            self.check_plan(done_r_stops)
