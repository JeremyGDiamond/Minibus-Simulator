import osmnx as ox
import networkx as nx


# additional data functions

def add_traverse_time(G):
    for n, nbrsdict in G.adjacency():
        for nbr, keydict in nbrsdict.items():
            for key, eattr in keydict.items():
                speed = G[n][nbr][key]['maxspeed']
                try:
                    speed = speed.replace(' mph', '')
                except:
                    speed = 30.0
                speed = float(speed) * 0.44704  # convert to meters/sec
                dist = G[n][nbr][key]['length']
                dist = float(dist)
                G[n][nbr][key]['traverse_time'] = float(round(dist / speed, 1))


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

# add speed limits to residential roads
add_default_speedlimits(suburb_map)
add_default_speedlimits(urbun_map)
add_default_speedlimits(test_map)

# calculate traversal time in m/s
add_traverse_time(suburb_map)
add_traverse_time(urbun_map)
add_traverse_time(test_map)

print(list(test_map.edges(data=True)))
print(list(test_map.nodes(data=True)))

ox.save_graphml(suburb_map, filename="suburb_map.graphml")
ox.save_graphml(urbun_map, filename="urbun_map.graphml")
ox.save_graphml(test_map, filename="test_map.graphml")
