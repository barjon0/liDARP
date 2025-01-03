from typing import List

from main.plan.Planner import Planner
from main.scope.Context import Context
from utils.demand import Request
from utils.network import Bus
from utils.plan import Route


class Core:
    def __init__(self, users: List[Request], network: List[Bus], schedule_mode: Context, solver: Planner):
        self.solver = solver
        self.schedule_mode = schedule_mode
        self.network = network
        self.users = users
        self.finished_schedule: List[Route] = []

    def start(self):
        pass


# main reads in the config file and then establishes core class -> control flow from there
def main():
    pass
