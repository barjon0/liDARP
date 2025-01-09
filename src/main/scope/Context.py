from datetime import time
from typing import Set, Dict

from utils.demand.Request import Request


class Context:
    def __init__(self, requests: Set[Request]):
        self.time_table = self.create_time_table(requests)

    def create_time_table(self, requests: Set[Request]):
        return None

    def start_context(self):
        pass

    # when trigger: receives curr. stand. from executor
    # gives curr. Standing + new requests to planner
    # waits some time for planning
    # give new plan to executor -> execute()
    def trigger_event(self):
        pass


class Static(Context):
    def __int__(self, requests: Set[Request]):
        super().__init__(requests)
