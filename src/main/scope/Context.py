from datetime import time
from typing import Set, Dict

from utils.demand import Request


class Context:
    def __init__(self, requests: Set[Request]):
        self.time_table = self.create_time_table(requests)

    def create_time_table(self, requests: Set[Request]) -> Dict[time, Set[Request]]:
        pass

    def start_context(self):
        pass

    # when trigger: receives curr. stand. from executor
    # gives curr. Standing + new requests to planner
    # waits some time for planning
    # give new plan to executor -> execute()
    def trigger_event(self):
        pass
