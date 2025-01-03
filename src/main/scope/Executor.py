from typing import Set, Dict

from utils.demand import Request
from utils.network import Stop, Bus
from utils.plan import Route


class Executor:
    def __init__(self):
        self.wait_users: Set[Request] = set()
        self.user_locations: Dict[Request, Stop] = {}
        self.passengers: Dict[Bus, Set[Request]] = {}
        self.bus_locations: Dict[Bus, Stop] = {}
        self.routes: Set[Route] = set()

    def handle_interrupt(self):
        pass

    def execute(self):
        pass