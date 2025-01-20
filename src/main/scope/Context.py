from datetime import time
from typing import Set, Dict

from main.plan.Planner import Planner
from main.scope.Executor import Executor
from utils.demand.Request import Request


class Context:
    def __init__(self, requests: Set[Request], executor: Executor, planner: Planner):
        self.time_table: Dict[time, Set[Request]] = self.create_time_table(requests)
        self.executor = executor
        self.planner = planner

    def create_time_table(self, requests: Set[Request]):
        NotImplementedError("instantiated abstract context class")

    def start_context(self):

        key_list = list(self.time_table.keys())
        for t in range(len(key_list) - 1):
            self.trigger_event(key_list[t], key_list[t+1])

        self.trigger_event(key_list[len(key_list) - 1])

    # when trigger: receives curr. stand. from executor
    # gives curr. Standing + new requests to planner
    # waits some time for planning
    # give new plan to executor -> execute()
    def trigger_event(self, time_now: time, time_next=None):
        curr_requests = self.time_table[time_now]
        curr_bus_locations = self.executor.bus_locations.copy()
        curr_user_locations = self.executor.user_locations.copy()
        curr_bus_delay = self.executor.bus_delay.copy()
        bus_user_dict = self.executor.passengers.copy()

        self.planner.make_plan(curr_requests, curr_bus_locations, bus_user_dict, curr_user_locations, curr_bus_delay)

        self.executor.execute_plan(self.planner.curr_routes, time_next)


class Static(Context):
    def __init__(self, requests: Set[Request], executor: Executor, planner: Planner):
        super().__init__(requests, executor, planner)

    def create_time_table(self, requests: Set[Request]):
        return {time(0, 0): requests}
