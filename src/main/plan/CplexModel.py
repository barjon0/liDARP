from typing import Set, List, Tuple, Dict

import Global
from main.plan.TimeConstraints import RelativeConstraints, AbsoluteValueConstraints
from utils.demand.AbstractRequest import Request, SplitRequest
from utils.helper import Helper, Timer
from utils.helper.EventGraph import EventGraph, IdleEvent, PickUpEvent
from utils.network.Bus import Bus
from utils.network.Line import Line
from utils.plan.Route import Route
from utils.plan.RouteStop import RouteStop


class CplexSolver:
    def __init__(self, event_graph: EventGraph, requests: Set[Request], bus_list: List[Bus]):
        self.event_graph = event_graph
        self.requests = requests
        self.buses = bus_list
        self.time_const_maker = RelativeConstraints()
        self.model = self.build_model()


    def build_model(self):
        #sys.path.append(Global.CPLEX_PATH)
        import cplex

        model = cplex.Cplex()
        # add variables
        # q_r for every request

        model.variables.add(names=[f'q_{x.id}' for x in self.requests],
                            types=[model.variables.type.binary] * len(self.requests))

        # z_i for route option
        for req in self.requests:
            for key in req.split_requests.keys():
                model.variables.add(names=[f'z_{req.id},{key}'], types=[model.variables.type.binary])

        # B_e for every split request (shared B_e variables) -> time of departure for split_request (drop-off/pick-up)
        for key in self.event_graph.request_dict:
            variable_args = self.time_const_maker.create_variables(key)
            model.variables.add(**variable_args[0])
            model.variables.add(**variable_args[1])

        # 2 * B_e per bus / not needed can actually infer from solution
        # for bus in self.buses:
        #    model.variables.add(names=[f'B_b{bus.id}+', f'B_b{bus.id}-'])

        # x_a for every edge
        for first in self.event_graph.edge_dict:
            for second in self.event_graph.edge_dict[first][1]:
                model.variables.add(names=[f'x_{first.id},{second.id}'], types=[model.variables.type.binary])

        lines = {x.line for x in self.buses}
        # set objective function: minimize distance covered but add penalty if request not accepted
        mulit = False

        if mulit:
            model.multiobj.set_num(2)

            # Objective 1 (priority 1)
            obj_pairs1 = [(f"q_{x.id}", -1) for x in self.requests]
            model.multiobj.set_linear(0, obj_pairs1)
            model.multiobj.set_priority(0, 2)

            # Objective 2 (priority 2)
            obj_pairs = []
            for first_event in self.event_graph.edge_dict.keys():
                for second_event in self.event_graph.edge_dict[first_event][1]:
                    obj_pairs += [(f"x_{first_event.id},{second_event.id}",
                                   Helper.calc_distance(first_event.location, second_event.location))]
            model.multiobj.set_linear(1, obj_pairs)
            model.multiobj.set_priority(1, 1)

            model.multiobj.set_sense(model.objective.sense.minimize)
        else:
            model.objective.set_sense(model.objective.sense.minimize)
            penalty = int(4 * Helper.calc_total_network_size(lines)) * len(self.requests) * len(self.buses) ** 2
            obj_pairs = [(f"q_{x.id}", -penalty) for x in self.requests]
            for first_event in self.event_graph.edge_dict.keys():
                for second_event in self.event_graph.edge_dict[first_event][1]:
                    obj_pairs += [(f"x_{first_event.id},{second_event.id}",
                                   Helper.calc_distance(first_event.location, second_event.location))]

            model.objective.set_linear(obj_pairs)

        # for all events: sum out - sum in = 0
        for key in self.event_graph.edge_dict.keys():
            var_names = [f'x_{x.id},{key.id}' for x in self.event_graph.edge_dict[key][0]] \
                        + [f'x_{key.id},{x.id}' for x in self.event_graph.edge_dict[key][1]]

            coeffs = [1] * len(self.event_graph.edge_dict[key][0]) + [-1] * len(self.event_graph.edge_dict[key][1])
            model.linear_constraints.add(
                lin_expr=[cplex.SparsePair(ind=var_names, val=coeffs)],
                senses=["E"],
                rhs=[0]
            )

        # for all split_options: sum of incoming edges x_a to first event >= z_i
        for req in self.requests:
            for option in req.split_requests:
                for split_req in req.split_requests[option]:
                    var_names = []
                    for event in self.event_graph.request_dict[split_req][0]:
                        var_names += [f"x_{x.id},{event.id}" for x in self.event_graph.edge_dict[event][0]]
                    var_names += [f"z_{req.id},{option}"]
                    coeffs = [1] * (len(var_names) - 1) + [-1]
                    model.linear_constraints.add(
                        lin_expr=[cplex.SparsePair(ind=var_names, val=coeffs)],
                        senses=["G"],
                        rhs=[0]
                    )

        # for line: sum of outgoing from idle <= number of buses
        for line in lines:
            amount = sum(1 for x in self.buses if x.line == line)
            idle_event = next(
                iter(x for x in self.event_graph.edge_dict.keys() if isinstance(x, IdleEvent) and x.line == line))

            var_names = [f"x_{idle_event.id},{x.id}" for x in self.event_graph.edge_dict[idle_event][1]]
            model.linear_constraints.add(
                lin_expr=[cplex.SparsePair(ind=var_names, val=[1] * len(var_names))],
                senses=["L"],
                rhs=[amount]
            )

        # think about idle_events!!!
        # add timing constraints for every bus(idle_event)
        for line in lines:
            idle_event = next(
                iter(x for x in self.event_graph.edge_dict.keys() if isinstance(x, IdleEvent) and x.line == line))

            # check incoming edges / previous event was drop-off
            var_dict: Dict[SplitRequest, List[str]] = {}
            for sub_event in self.event_graph.edge_dict[idle_event][0]:
                if sub_event.first in var_dict:
                    var_dict[sub_event.first] += [f"x_{sub_event.id},{idle_event.id}"]
                else:
                    var_dict[sub_event.first] = [f"x_{sub_event.id},{idle_event.id}"]

            for found_split in var_dict.keys():
                var_names = [f"B_{found_split.split_id}-"]
                duration = Timer.calc_time(Helper.calc_distance(found_split.drop_off_location, idle_event.location))
                coeffs = [duration] * len(var_dict[found_split]) + [1]
                model.linear_constraints.add(
                    lin_expr=[cplex.SparsePair(ind=var_dict[found_split] + var_names, val=coeffs)],
                    senses=["L"],
                    rhs=[line.end_time.get_in_minutes() - self.time_const_maker.add_value(found_split, False)]
                )

            # check outgoing edges / start at idle_event
            for sub_event in self.event_graph.edge_dict[idle_event][1]:
                if sub_event.first in var_dict:
                    var_dict[sub_event.first] += [f"x_{idle_event.id},{sub_event.id}"]
                else:
                    var_dict[sub_event.first] = [f"x_{idle_event.id},{sub_event.id}"]

            for found_split in var_dict.keys():
                var_names = [f"B_{found_split.split_id}+"]
                duration = Timer.calc_time(Helper.calc_distance(idle_event.location, found_split.pick_up_location))
                coeffs = [duration] * len(var_dict[found_split]) + [-1]
                model.linear_constraints.add(
                    lin_expr=[cplex.SparsePair(ind=var_dict[found_split] + var_names, val=coeffs)],
                    senses=["L"],
                    rhs=[-line.start_time.get_in_minutes() - Global.TRANSFER_MINUTES + self.time_const_maker.add_value(found_split, True)]
                )

        # make timing constraints for all subsequent splits in event_graph...(for doc look into thesis)
        for split_req in self.event_graph.request_dict.keys():

            for i in {0, 1}:
                var_dict: Dict[
                    Tuple[SplitRequest, bool], List[str]] = {}  # dict of form: {(request.id, type): [var_names]}
                for req_event in self.event_graph.request_dict[split_req][i]:
                    for sub_event in self.event_graph.edge_dict[req_event][1]:
                        if not isinstance(sub_event, IdleEvent):
                            if isinstance(sub_event, PickUpEvent):
                                type_bool = True
                            else:
                                type_bool = False
                            poss_tuple = (sub_event.first, type_bool)

                            if poss_tuple in var_dict:
                                var_dict[poss_tuple] += [f"x_{req_event.id},{sub_event.id}"]
                            else:
                                var_dict[poss_tuple] = [f"x_{req_event.id},{sub_event.id}"]

                for found_tuple in var_dict.keys():
                    other_split, type_bool = found_tuple
                    var_names = []
                    bool_first: bool
                    bool_second: bool
                    if i == 0:
                        split_first_location = split_req.pick_up_location
                        var_names += [f"B_{split_req.split_id}+"]
                        bool_first = True
                    else:
                        split_first_location = split_req.drop_off_location
                        var_names += [f"B_{split_req.split_id}-"]
                        bool_first = False

                    if type_bool:
                        split_sec_location = other_split.pick_up_location
                        var_names += [f"B_{other_split.split_id}+"]
                        bool_second = True
                    else:
                        split_sec_location = other_split.drop_off_location
                        var_names += [f"B_{other_split.split_id}-"]
                        bool_second = False

                    duration = Timer.calc_time(Helper.calc_distance(split_first_location, split_sec_location))
                    big_m = self.time_const_maker.get_big_m(split_req, bool_first, duration, self.time_const_maker.add_value(other_split, bool_second))
                    coeffs = [-big_m] * len(var_dict[found_tuple]) + [-1] + [1]

                    service_time = Global.TRANSFER_MINUTES * (int(bool(duration)))
                    model.linear_constraints.add(
                        lin_expr=[cplex.SparsePair(ind=var_dict[found_tuple] + var_names, val=coeffs)],
                        senses=["G"],
                        rhs=[service_time - big_m + duration + self.time_const_maker.add_value(split_req, bool_first)
                             - self.time_const_maker.add_value(other_split, bool_second)]
                    )

        for req in self.requests:
            found_tuples = set()
            for key in req.split_requests.keys():
                start_split = req.split_requests[key][0]
                end_split = req.split_requests[key][-1]
                if (start_split, end_split) not in found_tuples:
                    found_tuples |= {(start_split, end_split)}
                    var_names = [f"B_{start_split.split_id}+"]
                    max_ride_time = (req.latest_arr_time - req.latest_start_time).get_in_minutes()

                    # max ride time constraint
                    model.linear_constraints.add(
                        lin_expr=[cplex.SparsePair(ind=var_names + [f"B_{end_split.split_id}-"], val=[-1, 1])],
                        senses=["L"],
                        rhs=[max_ride_time + self.time_const_maker.add_value(start_split, True) - self.time_const_maker.add_value(end_split, False)]
                    )

                # add timing constraint for subsequent route stops
                for i in range(0, len(req.split_requests[key]) - 1):
                    prev_split = req.split_requests[key][i]
                    sub_split = req.split_requests[key][i + 1]
                    var_names = [f"B_{prev_split.split_id}-", f"B_{sub_split.split_id}+"]
                    model.linear_constraints.add(
                        lin_expr=[cplex.SparsePair(ind=var_names, val=[-1, 1])],
                        senses=["G"],
                        rhs=[self.time_const_maker.add_value(prev_split, False) - self.time_const_maker.add_value(sub_split, True)]
                    )

            # z variables for request sum to p_r
            var_names = [f"z_{req.id},{x}" for x in req.split_requests.keys()] + [f"q_{req.id}"]
            coeffs = [1] * len(req.split_requests.keys()) + [-1]
            model.linear_constraints.add(
                lin_expr=[cplex.SparsePair(ind=var_names, val=coeffs)],
                senses=["E"],
                rhs=[0]
            )

        return model

    def solve_model(self):
        # self.model.parameters.randomseed.set(2)
        # self.model.write("model.lp")

        self.model.parameters.mip.tolerances.mipgap.set(0.01)
        self.model.parameters.threads.set(8) # specify number of threads
        self.model.parameters.workmem.set(27000)  # Up to 27 GB of RAM
        self.model.parameters.timelimit.set(900)

        #self.model.parameters.emphasis.mip.set(3)

        self.model.parameters.mip.strategy.nodeselect.set(2) # (check 1-3)select strategy for selecting node for branching
        self.model.parameters.mip.strategy.variableselect.set(0) #(check 0 /-1 - 4) select on which variable to branch on

        self.model.parameters.mip.strategy.lbheur.set(0)  # check(0,1)local branching heuristic
        self.model.parameters.mip.strategy.heuristicfreq.set(0) # (check 0/-1) disable use of heuristic
        self.model.parameters.mip.strategy.rinsheur.set(0)  # 50 = apply every 50 nodes
        self.model.parameters.preprocessing.presolve.set(1) # decide if presolve heuristic is used
        self.model.parameters.preprocessing.numpass.set(-1) # check(-1, 0) limits number of presolves
        # self.model.parameters.mip.strategy.presolvenode.set(2) # check(0, -1, 3) decides if presolve at node

        #self.model.parameters.mip.cuts.nodecuts.set(3)
        #self.model.parameters.mip.cuts.flowcovers.set(2)
        #self.model.parameters.mip.cuts.gomory.set(2)
        #self.model.parameters.mip.cuts.mircut.set(2)
        #self.model.parameters.mip.cuts.implied.set(-1)
        #self.model.parameters.mip.cuts.localimplied.set(-1)
        #self.model.parameters.mip.cuts.disjunctive.set(2)  # check(0 -1 - 3) choose to use more aggressive cuts

        var_names = self.model.variables.get_names()
        var_names_set = set(var_names)
        if len(var_names) != len(var_names_set):
            print("There are duplicate variable names")
        self.model.parameters.mip.display.set(3)    # set extent of logging
        self.model.solve()
        print("Objective Value: " + str(self.model.solution.get_objective_value()))

    def convert_to_plan(self):
        # for every bus -> start at idle_event and walk along path
        # -> (build RouteStop, check when finished!!, add users to pick-up and drop-off and times)
        request_order = list(self.requests)
        solution_ints = self.model.solution.get_values([f"q_{x.id}" for x in request_order])
        combi = []
        for i in range(len(request_order)):
            combi.append(f"Request: {request_order[i].id} has value {solution_ints[i]}")

        line_set: Set[Line] = {x.line for x in self.buses}
        line_bus_dict: Dict[Line, List[Bus]] = {x: [y for y in self.buses if y.line == x] for x in line_set}
        all_plans: List[Route] = []

        for line in line_bus_dict.keys():
            idle_event: IdleEvent = next(
                iter(x for x in self.event_graph.edge_dict.keys() if isinstance(x, IdleEvent) and x.line == line))
            edge_vals = self.model.solution.get_values(
                [f"x_{idle_event.id},{x.id}" for x in self.event_graph.edge_dict[idle_event][1]])
            round_edge_vals = [round(x) for x in edge_vals]
            for i in range(len(line_bus_dict[line])):
                bus = line_bus_dict[line][i]
                bus_plan = Route(bus)

                # i is curr. bus idx(starting at 0)
                counter = -1  # counter for amount of 1s already found
                j = -1              # j iterates over edge values
                while counter < i and j < len(round_edge_vals) - 1:         # if
                    j += 1
                    if round_edge_vals[j] == 1:
                        counter += 1
                # if counter is smaller then i => no 1 found so bus just stays in place
                if counter < i:
                    bus_plan.stop_list.append(
                        RouteStop(idle_event.location, bus.line.start_time, bus.line.end_time, bus))
                else:
                    next_event = self.event_graph.edge_dict[idle_event][1][j]
                    time_var = self.model.solution.get_values(f"B_{next_event.first.split_id}+")

                    duration = Timer.calc_time(Helper.calc_distance(idle_event.location, next_event.location))
                    curr_route_stop = RouteStop(idle_event.location, bus.line.start_time,
                                                Timer.create_time_object(time_var - Global.TRANSFER_MINUTES - duration
                                                + self.time_const_maker.add_value(next_event.first, True)), bus)

                    while next_event is not idle_event:
                        # check selected option for request -> if event fits with option:
                        z_options = list(next_event.first.parent.split_requests.keys())
                        z_options_vals = self.model.solution.get_values(
                            [f"z_{next_event.first.id},{x}" for x in z_options])
                        z_options_vals_round = [round(x) for x in z_options_vals]
                        if 1 in z_options_vals_round and next_event.first in next_event.first.parent.split_requests[
                            z_options[z_options_vals_round.index(1)]]:

                            if next_event.location != curr_route_stop.stop:
                                bus_plan.stop_list.append(curr_route_stop)

                                duration = Timer.calc_time(
                                    Helper.calc_distance(curr_route_stop.stop, next_event.location))
                                if isinstance(next_event, PickUpEvent):
                                    time_var = self.model.solution.get_values(f"B_{next_event.first.split_id}+")
                                    curr_route_stop = RouteStop(next_event.location,
                                                                curr_route_stop.depart_time.add_minutes(duration),
                                                                Timer.create_time_object(time_var + self.time_const_maker.add_value(next_event.first, True)), bus)
                                    curr_route_stop.pick_up.add(next_event.first.parent)
                                else:
                                    time_var = self.model.solution.get_values(f"B_{next_event.first.split_id}-")
                                    curr_route_stop = RouteStop(next_event.location,
                                                                curr_route_stop.depart_time.add_minutes(duration),
                                                                Timer.create_time_object(time_var + self.time_const_maker.add_value(next_event.first, False)), bus)
                                    curr_route_stop.drop_off.add(next_event.first.parent)
                            else:
                                if isinstance(next_event, PickUpEvent):
                                    time_var = (self.model.solution.get_values(f"B_{next_event.first.split_id}+")
                                                + self.time_const_maker.add_value(next_event.first, True))
                                    curr_route_stop.pick_up.add(next_event.first.parent)
                                else:
                                    time_var = (self.model.solution.get_values(f"B_{next_event.first.split_id}-")
                                                + self.time_const_maker.add_value(next_event.first, False))
                                    curr_route_stop.drop_off.add(next_event.first.parent)

                                curr_route_stop.depart_time = Timer.create_time_object(time_var)
                        else:
                            print(f"Unnecessary event removed: {next_event}")

                        edge_vals = self.model.solution.get_values(
                            [f"x_{next_event.id},{x.id}" for x in self.event_graph.edge_dict[next_event][1]])
                        next_round_edge_vals = [round(x) for x in edge_vals]
                        next_event_idx = next_round_edge_vals.index(1)
                        next_event = self.event_graph.edge_dict[next_event][1][next_event_idx]

                    # handle final idle_event stop
                    bus_plan.stop_list.append(curr_route_stop)
                    duration = Timer.calc_time(Helper.calc_distance(curr_route_stop.stop, next_event.location))
                    bus_plan.stop_list.append(
                        RouteStop(next_event.location, curr_route_stop.depart_time.add_minutes(duration),
                                  bus.line.end_time, bus))
                all_plans.append(bus_plan)

        return all_plans
