# Writing Sample: Mini Bus Engine

# Background

My project is based on and idea from a 1977 architecture textbook called a pattern language. The book is generally thought to be the originator of the idea a pattern center design in software engineering and as such is considered highly influential in many software and ux design fields.

![Writing%20Sample%20Mini%20Bus%20Engine%2083231184014d40009dd4d65fc786dd2c/Screenshot_from_2019-12-04_09-09-13.png](Writing%20Sample%20Mini%20Bus%20Engine%2083231184014d40009dd4d65fc786dd2c/Screenshot_from_2019-12-04_09-09-13.png)

Pattern number 20 is called a minibus. A minibus is a vehicle which is dynamically routed between hundreds of optional bus stops with six passengers. Mini buses are thought to be useful in providing efficient and fast public transit to areas which are geographically large, with low population densities.

# Goal

The goal of this project will be to make a mini bus simulator where the buses are both assigned and routed according to heuristics in graph theory. The assignment here a stick will be the most variable. For assignment I will be experimenting with random assignment, checking bus distance from a given passenger using algorithm A*, and generating triangles from the start and end points of a passenger's destination and a bus is starting position and then taking the triangle area.

# Open Street maps data retrieval Design

In the first section of this project I use an existing anaconda environment called [OSMnx](https://github.com/gboeing/osmnx), published by professor Geoff Boeing of the University of Southern California, to download geographic data from Open Street Maps and insert it into a graph from the python library networkx. Doing this I generate three graphs based on data from the Denver metro area. First a 3 by 3 block area which is used as a test map.  

![Writing%20Sample%20Mini%20Bus%20Engine%2083231184014d40009dd4d65fc786dd2c/Figure_3.png](Writing%20Sample%20Mini%20Bus%20Engine%2083231184014d40009dd4d65fc786dd2c/Figure_3.png)

Then a geographically larger area which encloses the suburb I grew up in. 

![Writing%20Sample%20Mini%20Bus%20Engine%2083231184014d40009dd4d65fc786dd2c/Figure_2.png](Writing%20Sample%20Mini%20Bus%20Engine%2083231184014d40009dd4d65fc786dd2c/Figure_2.png)

Finally a map of the urban center of downtown Denver bounded by major roads on all four sides.

![Writing%20Sample%20Mini%20Bus%20Engine%2083231184014d40009dd4d65fc786dd2c/Figure_1.png](Writing%20Sample%20Mini%20Bus%20Engine%2083231184014d40009dd4d65fc786dd2c/Figure_1.png)

## OSMnxTest python implementation

This there are essentially 3 sections to this script. The first part of the main is the section that defines the bounds of the graphs, removes disconnected nodes, and plots them in matplotlib.

```python
# define a bounding box in urban downtown denver
north, south, east, west = 39.7803119, 39.725, -104.9405181, -105.0171331

# # create network from that bounding box
urbun_map = ox.graph_from_bbox(north, south, east, west, network_type='drive')
urbun_map.remove_nodes_from(nx.isolates(urbun_map))
urbun_map = ox.project_graph(urbun_map)
ox.plot_graph(urbun_map)

# define a bounding box in the chosen suburb of denver
north2, south2, east2, west2 = 39.86, 39.84, -105.05, -105.09

# create network from that bounding box
suburb_map = ox.graph_from_bbox(north2, south2, east2, west2, network_type='drive')
suburb_map.remove_nodes_from(nx.isolates(suburb_map))
suburb_map = ox.project_graph(suburb_map)
ox.plot_graph(suburb_map)

# define a bounding box in the chosen test location
north3, south3, east3, west3 = 39.7449719,  39.7399155, -104.9734466, -104.9788795

# create network from that bounding box
test_map = ox.graph_from_bbox(north3, south3, east3, west3, network_type='drive')
test_map.remove_nodes_from(nx.isolates(test_map))
test_map = ox.project_graph(test_map)
ox.plot_graph(test_map)
```

Then I have 2 functions that add some missing data. Open Street Maps dosen't have recorded speed limits for every road. I use the following function traverse every edge in the graph and add the default speed limit as an attribute.

```python
def add_default_speedlimits(G):
    except_count = 0
    not_except_count = 0

    for n, nbrsdict in G.adjacency():
        for nbr, keydict in nbrsdict.items():
            for key, eattr in keydict.items():
                try:
                    G[n][nbr][key]['maxspeed']
                    not_except_count = not_except_count + 1
                except:
                    G[n][nbr][key]['maxspeed'] = '30 mph'
                    except_count = except_count + 1

    print(nx.number_of_edges(G))
    print(except_count)
    print(not_except_count)
```

By similar method I then add an attribute to each edge that is (length of the edge / speed limit) called traverse_time this will be used as the weight for the path search later so that my paths can be measured in time. both of these functions are based on [this page of the networkx documentation](https://testfixsphinx.readthedocs.io/en/latest/reference/classes.multigraph.html)

lastly I write these graphs to a file in the graphml format, native to OSMnx. This is a formatted xml filetype that can store complex graphs.

```python
ox.save_graphml(suburb_map, filename="suburb_map.graphml")
ox.save_graphml(urbun_map, filename="urbun_map.graphml")
ox.save_graphml(test_map, filename="test_map.graphml")
```

The default output of these files render all edge and node attributes as strings so it is necessary to go int the .graphml files and change traverse_time to a double for the simulation to run properly. note the attribute type in line 3 below

```xml
graphml.graphdrawing.org/xmlns/1.0/graphml.xsd">
  <key id="d18" for="edge" attr.name="ref" attr.type="string" />
  <key id="d17" for="edge" attr.name="traverse_time" attr.type="double" />
  <key id="d16" for="edge" attr.name="maxspeed" attr.type="string" />
  <key id="d15" for="edge" attr.name="geometry" attr.type="string" />
  <key id="d14" for="edge" attr.name="length" attr.type="string" />
```

# Simulation Design

This runs as if a set of agents spawn, simulates how long it would take them to drive to their destinations and saves the average, uses a given heuristic to assign each agent to a bus with an open seat, and then uses a compound path heuristic to simulate the path the bus will take to service every passenger, then takes the average of the buses traversal time divided by the number of passengers. I decided to use the same compound path heuristic to test all assignment heuristics against thus making the assignment heuristic the independent variable. 

# Simulation implementation

## class definitions

The agent class simply holds it's data as an abstract data type. The minibus class contains functions that handle adding passengers, nodes to the queue to be visited, finding the route with the routing heuristic, and returning the total path traverse time.

 

```python
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
```

I then have a series of functions that handle the functions of a simulation.

```python
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
```

Next I define all of the heuristics. The first and simplest is selects a random bus with an open seat and adds the agent to it.

```python
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
```

The nest one finds the open bus with the closest path to the agents start node. For run time sake I only select from a random subset of 15 buses (see the for loop that populates the list subset buses. In my small scale tests that didn't have a large effect on the data.

```python
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
```

The last, and most creative in my opinion, defines a triangle with the x and y values of the 3 nodes (agent.start, agent.end and bus.start) and selects the open bus with the triangle of smallest area. unfortunately this one has to high a run time cost as it is currently implemented and trued out not to be scaleless on the level of the others thus it was omitted from tests.

```python
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
```

I then have functions which run the simulation given a series of perimeters and a functions that outputs the data as .csv files.

```python
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
```

lastly the main function tests h1 and h2 at different bus concentrations at both the suburban and urban scales

```python
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
```

*this is all of the code

# Analysis

## Expected results

giving the number of variables at play it's difficult to make a solid prediction on performance compared to cars. One of the main advantages transit vehicles tend to have is they get dedicated infrastructure and can be routed around traffic. Without those factors at play cars may have a performance edge that can't be overcome. I do expect there will be a sweet spot in the bus concentration graph where they close the performance gap substantially. this sweet spot will ideally be before the number of buses is above .75 the number of cars since the broader goal of transit systems is to reduce the number of vehicles on the road. 

## Results

The aggregate of my data is this table.

[MBE data - Sheet1](https://www.notion.so/082043eab4db4327a7a4a72992238a25)

When you graph travel time verses number of buses per person clear patterns emerge

![Writing%20Sample%20Mini%20Bus%20Engine%2083231184014d40009dd4d65fc786dd2c/pubchart.png](Writing%20Sample%20Mini%20Bus%20Engine%2083231184014d40009dd4d65fc786dd2c/pubchart.png)

First H2 out preforms H1 (random assignment) in both suburban and urban environments. Second without the inherent advantages of dedicated transit infrastructure cars simply out preform transit in all cases. Lastly the buses performance asymptotically approach the performance of cars and as such there are diminishing returns to adding more buses beyond 0.5 buses per person.

# Conclusions

There are a million directions I can take this project in the future. My main objectives are getting H3 working, multi-threading the simulation run function, and adding a real time clock. The data is promising and indicates there is potential for further optimization to make mini buses a plausible replacement to some traditional transit options.