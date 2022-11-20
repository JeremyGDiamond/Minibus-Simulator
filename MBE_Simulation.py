from sympy import Point, Polygon
import csv
import time
import osmnx as ox
import networkx as nx
import random
from statistics import mean, StatisticsError
from threading import Thread


# simulation classes

class Agent:
    def __init__(self, G):
        nodes = list(G.nodes())
        self.start = random.choice(nodes)
        self.end = random.choice(nodes)
        while (self.end == self.start):
            self.end = random.choice(nodes)


class Mini_Bus:
    def __init__(self, G):
        nodes = list(G.nodes())
        self.node_list = [random.choice(nodes)]
        self.passenger_list = []

    def add_node_to_list(self, node):
        self.node_list.append(node)

    def add_passenger(self, agent):

        self.passenger_list.append(agent)

        if not (agent.start in self.node_list):
            self.add_node_to_list(agent.start)

        if not (agent.end in self.node_list):
            self.add_node_to_list(agent.end)

    def find_route(self):
        # next shortest method
        current_node = self.node_list[0]

        route = [current_node]
        current_list = []
        next_list = []

        self.node_list.remove(current_node)

        while not (len(current_list) == 0):
            dist_from_current = nx.shortest_path_length()

    def get_traverse_time(self, G):
        total = 0.0
        for elem in range(len(self.node_list)):
            try:
                total = total + nx.shortest_path_length(G, self.node_list[elem], self.node_list[elem + 1],
                                                        weight='traverse_time')
            except:
                return total


# simulation functions

def load_graph(name):
    return ox.load_graphml(name)


def generate_agents(G, proportion):
    num_agents = round(((nx.number_of_nodes(G)) * proportion))
    agents = []
    for i in range(num_agents):
        agents.append(Agent(G))

    return agents


def car_traverse(G, agent):
    route_time = nx.shortest_path_length(G, agent.start, agent.end, weight='traverse_time')

    return route_time


def generate_buses(G, proportion, agent_num):
    num_buses = round(((nx.number_of_nodes(G)) * proportion))
    buses = []
    for i in range(num_buses):
        buses.append(Mini_Bus(G))

    return buses


def bus_assignment_h1(agent, max, buses):
    open_buses = []

    for bus in buses:
        if len(bus.passenger_list) < max:
            open_buses.append(bus)

    try:
        bus = random.choice(open_buses)
    except IndexError:
        pass
    try:
        bus.add_passenger(agent)
    except:
        pass


def bus_assignment_h2(G, agent, max, buses):
    open_buses = []

    for bus in buses:
        if len(bus.passenger_list) < max:
            open_buses.append(bus)

    subset_buses = []
    for i in range (15):
        subset_buses.append(random.choice(open_buses))

    closest_start_bus = subset_buses[0]

    # default value is needed
    closest_start_dist = 1e20 + 1

    # cache value to save cycels
    try:
        closest_start_dist = nx.shortest_path_length(G, closest_start_bus.node_list[0], agent.start, weight='traverse_time')

    except:
        pass

    for bus in subset_buses:
        try:
            new_dist = nx.shortest_path_length(G, bus.node_list[0], agent.start, weight='traverse_time')
        except:
            # number so big it will never be selected
            new_dist = 1e20

        if new_dist < closest_start_dist:
            closest_start_dist = new_dist
            closest_start_bus = bus

    closest_start_bus.add_passenger(agent)


def bus_assignment_h3(G, agent, max, buses):
    open_buses = []

    y1 = G.nodes[agent.start]['y']
    y2 = G.nodes[agent.end]['y']

    x1 = G.nodes[agent.start]['x']
    x2 = G.nodes[agent.end]['x']

    p1, p2 = [(x1, y1), (x2, y2)]

    for bus in buses:
        if len(bus.passenger_list) < max:
            open_buses.append(bus)
    try:
        shortest_dist_bus = open_buses[0]
    except IndexError:
        return

    smallest_tri_size = 1e20

    for bus in open_buses:
        bx = G.nodes[bus.node_list[0]]['x']
        by = G.nodes[bus.node_list[0]]['y']
        p3 = (bx, by)

        try:
            poly = abs(Polygon(p1, p2, p3).area)
        except:
            shortest_dist_bus = bus
            break

        if smallest_tri_size > poly:
            smallest_tri_size = poly
            shortest_dist_bus = bus

    shortest_dist_bus.add_passenger(agent)


def run(mode, proportion_buses, map_name, max):
    G = load_graph(map_name)

    number_of_agents = nx.number_of_nodes(G)

    agents = generate_agents(G, 0.1)

    car_traverse_times = []

    for agent in agents:
        try:
            car_traverse_times.append(car_traverse(G, agent))
        except:
            pass

        bus_list = generate_buses(G, proportion_buses, number_of_agents)

        if mode == 1:
            for agent in agents:
                bus_assignment_h1(agent, max, bus_list)

        elif mode == 2:
            for agent in agents:
                bus_assignment_h2(G, agent, max, bus_list)

        elif mode == 3:
            for agent in agents:
                bus_assignment_h3(G, agent, max, bus_list)

    bus_traverse_times = []

    for bus in bus_list:
        if len(bus.node_list) > 1:
            bus_traverse_times.append(bus.get_traverse_time(G))

    averages = (mean(car_traverse_times), mean(bus_traverse_times))

    return averages


def output_data(name, data):
    iteration = ["iteration"]
    car_time = ["car_time"]
    bus_time = ["bus_time"]

    for elem in data:
        iteration.append(elem[0])
        car_time.append(elem[1][0])
        bus_time.append(elem[1][1])

    row_list = [iteration, car_time, bus_time]

    with open(name, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(row_list)

def threadRun(mode, proportion_buses, map_name, max, avg):
    G = load_graph(map_name)

    number_of_agents = nx.number_of_nodes(G)

    agents = generate_agents(G, 0.1)

    car_traverse_times = []

    for agent in agents:
        try:
            car_traverse_times.append(car_traverse(G, agent))
        except:
            pass

        bus_list = generate_buses(G, proportion_buses, number_of_agents)

        if mode == 1:
            for agent in agents:
                bus_assignment_h1(agent, max, bus_list)

        elif mode == 2:
            for agent in agents:
                bus_assignment_h2(G, agent, max, bus_list)

        elif mode == 3:
            for agent in agents:
                bus_assignment_h3(G, agent, max, bus_list)

    bus_traverse_times = []

    for bus in bus_list:
        if len(bus.node_list) > 1:
            bus_traverse_times.append(bus.get_traverse_time(G))

    print((mean(car_traverse_times), mean(bus_traverse_times)))
    avg = (mean(car_traverse_times), mean(bus_traverse_times))

    # return averages


# fuctionality test
avg = run(1, 0.2, "test_map.graphml", 6)

print(avg)

avg = run(2, 0.2, "test_map.graphml", 6)

print(avg)

testData = [(0.2, avg)]

output_data("test.csv", testData)

suburb_random = []
suburb_close_start = []

urbun_random = []
urbun_close_start = []
#
# # suburb runs
for i in range(1, 9):
    avg = run(1, i * .025, "suburb_map.graphml", 6)

    print((i * .025, avg))
    suburb_random.append((i * .025, avg))

    start_time = time.time()
    avg = run(2, i * .025, "suburb_map.graphml", 6)
    print("h2 time: " + str(time.time() - start_time))

    print((i * .025, avg))
    suburb_close_start.append((i * .025, avg))

output_data("suburb_random.csv", suburb_random)
output_data("suburb_close_start.csv", suburb_close_start)

# urbun runs
for i in range(1, 9):
    avg = run(1, i * .025, "urbun_map.graphml", 6)

    print((i * .025, avg))
    urbun_random.append((i * .025, avg))

    start_time = time.time()
    avg = run(2, i * .025, "urbun_map.graphml", 6)
    print("h2 time: " + str(time.time() - start_time))

    print((i * .025, avg))
    urbun_close_start.append((i * .025, avg))

output_data("urbun_random.csv", urbun_random)
output_data("urbun_close_start.csv", urbun_close_start)


