import numpy as np
import pandas as pd
import osmnx as ox
import networkx as nx
from geopandas import gpd
from osmnx import graph_to_gdfs, graph_from_gdfs
import psycopg2
import psycopg2.extras
import csv
from db import con
from datetime import datetime
import json
from shapely.geometry import shape, Polygon

# for some reason this prevents the db for getting upset with "duplicate values" in candidate_edges. probable a concurrency issue
con.autocommit = True

# a shortcut to execute a query and return all results
def exe_fetch(cursor, query):
    cursor.execute(query)
    return cursor.fetchall()

# a shortcut to execute a query and return first result
def exe_fetchone(cursor, query):
    cursor.execute(query)
    return cursor.fetchone()

# a safe get[0] for a tuple (or a list)
def get_first(tuple):
    return 0 if tuple is None else tuple[0]

# commented this out because I don't want to get a specific position
# address = '731 Park Avenue, Huntington NY, 11743'
# G = ox.get_undirected(ox.graph_from_address(address, network_type='drive', dist=3000, retain_all=True))

# This is the first statement. It gets a graph from OpenStreetMap based on the geocodable area retrieved from the user.
name = input("Choose city or area:")
download = datetime.now()
G = ox.get_undirected(ox.graph_from_place(name, network_type='drive', retain_all=True))
# G = ox.get_undirected(ox.graph_from_place(name, custom_filter='["highway"~"motorway|trunk"]', retain_all=True))
# G = ox.get_undirected(ox.graph_from_place(name, custom_filter='["highway"~"motorway"]', retain_all=True))
# G = ox.get_undirected(ox.graph_from_place(name, custom_filter='["highway"~"primary|trunk"]', retain_all=True))
# G = ox.get_undirected(ox.graph_from_place(name, custom_filter='["highway"~"motorway|primary|trunk"]', retain_all=True))
# G = ox.get_undirected(ox.graph_from_place(name, custom_filter='["highway"~"motorway|primary|trunk|secondary"]', retain_all=True))
# G = ox.get_undirected(ox.graph_from_place(["Brooklyn, NY","Queens, NY", "Nassau County, NY", "Suffolk County, NY"], custom_filter='["highway"~"motorway|primary|trunk|secondary|tertiary"]', retain_all=True))

# # https://medium.com/@pramukta/recipe-importing-geojson-into-shapely-da1edf79f41d
# with open("shape/oysterbay-glencove.geojsonl.json") as f:
#   feature = json.load(f)

# # print(feature['geometry'])
# # print([shape(feature["geometry"]).buffer(0) for feature in features])

# # # NOTE: buffer(0) is a trick for fixing scenarios where polygons have overlapping coordinates 
# north_shore = Polygon(shape(feature['geometry']))

# G = ox.get_undirected(ox.graph_from_polygon(north_shore,network_type='drive',retain_all=True))

#don't need to plot this below bc it holds the thing up
# fig, ax = ox.plot_graph(G, figsize=(10,10), node_color='orange', node_size=30,
# node_zorder=2, node_edgecolor='k')
print("processing has begun",f"nodes: {G.number_of_nodes()}", f"edges: {G.number_of_edges()}")
beginning = datetime.now()
print(f"download time: {beginning - download}")
# imports the graph into the databate and processes the graph
with con.cursor() as cursor:

    cursor.execute(f"INSERT INTO location VALUES ('{name}')")

    #For each node, inserts into the "node" table.
    #The "node" table has "id", "lat", and "lon" columns
    psycopg2.extras.execute_values(cursor, """
        INSERT INTO node(id, lat, lon, loc) VALUES %s;
    """, ((
        n,
        data['y'],
        data['x'],
        name
    ) for n, data, in G.nodes(data=True)))

    #For each node, inserts the node with itself as its parent and 0 as its phase into the "graph_phase" table
    #The "graph_phase" table has the columns "phase", "node_id", "parent", and "traversed"
    #Through the process of this script, sets of nodes (i.e. subgraphs) with different parents in one phace will receive different parents in the next phase until it is not possible to continue this operation.
    psycopg2.extras.execute_values(cursor, """
        INSERT INTO graph_phase(phase, node_id, parent, loc) VALUES %s;
    """, ((
        0,
        n,
        n,
        name
    ) for n, data, in G.nodes(data=True)))

    #For each edge, inserts "from" node, "to" node, and edge "length"
    psycopg2.extras.execute_values(cursor, """
        INSERT INTO edge("from", "to", length, loc) VALUES %s;
    """, ((
        u,
        v,
        data['length'],
        name
    ) for u, v ,keys, data in G.edges(data=True, keys=True)))

    #sets the current phase to 0. This is the phase of all records in "graph_phase" at this point 
    ph = 0
    rounds = []


    #this operation will add a set of records into graph_phase identical to f"select * from graph_phase where phase = {ph}", except that the phase will be incremented by one. 
    #then, subgraphs (sets of nodes in graph_phase same parents) will be joined (get the same parent) through nodes which have the smallest product of (length of node * length of join-candidate subgraph with smallest length). These two candidate subgraphs will then be joined under the same parent (using the smallest parent_id) and then all nodes of this new subgraph will become "traversed" = true.
    #the while loop will end when all nodes have the same parent. this is unlikely because in large road network graphs there may be several disconnected subgraphs. It's more likely that the break statement if(len(working) < 1): will cause the loop to end, because there are no nodes that can be further joined.
    # #I just realized that the traversed = false below makes the algo exit too early. 
    while(len(exe_fetch(cursor, f"select distinct parent from graph_phase where phase = {ph}")) > 1):
        print("begin")

        phasebegin = datetime.now()

        last = exe_fetch(cursor, f"select * from graph_phase where phase = {ph}")
        working = exe_fetch(cursor, f"""
            select edge.id, fromphase.parent, tophase.parent from edge 
            join node as "from" on edge.from = "from".id and edge.loc = "from".loc
            join node as "to" on edge.to = "to".id and edge.loc = "to".loc
            join graph_phase as fromphase on "from".id = fromphase.node_id and "from".loc = fromphase.loc
            join graph_phase as tophase on "to".id = tophase.node_id and "to".loc = tophase.loc and fromphase.phase = tophase.phase
            where fromphase.parent <> tophase.parent
            and edge.loc = '{name}'
            and fromphase.phase={ph} 
            limit 1;
            """) #left out the traversed part
        if(len(working) < 1):
            print("nowork")
            break

        # increments phase
        ph = ph+1
        # inserts new graph phase
        cursor.execute(f"""
            INSERT INTO graph_phase("phase", "node_id", "parent", "loc") 
            (select {ph}, node_id, parent, loc from graph_phase where phase = {ph - 1});
        """)
        # print(f"Phase {ph}")

        #network size stores the length of subgraphs used in this algorithm. 
        cursor.execute(
            f"""
            insert into network_size 
            (select graph_phase.parent, graph_phase.loc, sum(edge.length) as sum_length, graph_phase.phase
            from graph_phase 
            join edge on (graph_phase.node_id = edge.from and graph_phase.loc = edge.loc) 
            or (graph_phase.node_id = edge.to and graph_phase.loc = edge.loc) 
            where graph_phase.phase={ph}
            and graph_phase.loc = '{name}' 
            group by graph_phase.parent, graph_phase.loc, graph_phase.phase) 
            
            """
        )
        
        #don't think this is necessary
        # print(ph, len(exe_fetch(cursor, f"""
        #     select edge.id, fromphase.parent, tophase.parent from edge 
        #     join node as "from" on edge.from = "from".id
        #     join node as "to" on edge.to = "to".id    
        #     join graph_phase as fromphase on "from".id = fromphase.node_id
        #     join graph_phase as tophase on "to".id = tophase.node_id and fromphase.phase = tophase.phase
        #     where fromphase.parent <> tophase.parent 
        #     and fromphase.phase={ph} 
        #     and fromphase.traversed = false;
        # """)))

        # gets new candidates 
        # {name} is an easy way to return the loc in the select statement
        cursor.execute(f"""
        insert into candidate_edge(gateway_size, fromparent, toparent, loc, phase) (select (power(10,avg(log(edge.length))) * least(fromnetwork.sum_length,  tonetwork.sum_length))/ count(*) as gateway_size, fromphase.parent, tophase.parent, '{name}', {ph} from edge
        join graph_phase as fromphase on edge.from = fromphase.node_id and edge.loc = fromphase.loc
        join graph_phase as tophase on edge.to = tophase.node_id and edge.loc = tophase.loc and fromphase.phase = tophase.phase
        join network_size as fromnetwork on fromnetwork.parent = fromphase.parent and fromnetwork.loc = fromphase.loc and fromnetwork.phase = fromphase.phase
        join network_size as tonetwork on tonetwork.parent = tophase.parent and tonetwork.loc = tophase.loc and tonetwork.phase = tophase.phase
        where fromphase.parent <> tophase.parent
        and fromphase.phase={ph}
        and edge.loc = '{name}'
        group by fromphase.parent, tophase.parent, fromnetwork.sum_length, tonetwork.sum_length
        order by gateway_size);
        """)

        #deletes old candidates
        # cursor.execute("delete from candidate_edge;")

        #inserts new candidates (no longer necessary because execute above)
        # psycopg2.extras.execute_values(cursor, """
        #     INSERT INTO candidate_edge VALUES %s;
        # """, candidates)
        #there should be no need for on conflict if i am inserting after deleting all records
        # had the same insert network statement twice lol

        while(True):
            print("iteration")
            #the algorithm described above is executed here
            cursor.execute(f"""
            select candidate_edge.fromparent, candidate_edge.toparent, candidate_edge.gateway_size from candidate_edge
            join graph_phase as fromphase on candidate_edge.fromparent = fromphase.node_id and candidate_edge.phase = fromphase.phase
            join graph_phase as tophase on candidate_edge.toparent = tophase.node_id and tophase.phase = fromphase.phase
            where candidate_edge.phase = {ph}
            and candidate_edge.loc = '{name}'
            and not fromphase.traversed
            and not tophase.traversed
            order by candidate_edge.gateway_size
            limit 1;
            """)
            # combine_edges.from <> combine_edges.to prevents culdesacs from messing the procedure up

            #zero represents the node that will join two subgraphs together.
            zero = cursor.fetchone()
            print("zero", zero)

            #if there is no node that can join subgraphs together, this will not execute.
            if(not zero):
                break
            
            # prints nodes that are updated
            print(exe_fetch(cursor, f"""
            update graph_phase set parent = {min(zero[0],zero[1])}, traversed = true where parent in ({zero[0]},{zero[1]}) and phase = {ph} and loc = '{name}' returning *;
            """))
        

        # # increments phase
        # ph = ph+1
        print(ph)

        rounds.append(datetime.now()-phasebegin)
    
    for idx, val in enumerate(rounds):
        print(idx+1, val)
    print(f"nodes: {G.number_of_nodes()}", f"edges: {G.number_of_edges()}")
    print("processing complete: HMS=", datetime.now() - beginning)
    print(f"download time: {beginning - download}")

    # mycolors = []
    # graph_edges = G.edges
    # for i in graph_edges:
    #     G[i[0]][i[1]][i[2]]['color'] = get_first(cursor, exe_fetchone(cursor, f"select min(fromphase.phase) from edge join graph_phase as fromphase on edge.from = fromphase.node_id join graph_phase as tophase on edge.to = tophase.node_id and tophase.phase =fromphase.phase where fromphase.parent = tophase.parent and edge.from = {i[0]} and edge.to = {i[1]} group by edge.id;"))
        # mycolors.append(G[i[0]][i[1]][i[2]]['color'])

    # ec = ox.plot.get_edge_colors_by_attr(G, attr='color')


    graph_nodes = G.nodes
    max_phase = exe_fetchone(cursor, f"select max(phase) from graph_phase where loc = '{name}'")[0]
    # adds parent properties from the "graph_nodes" table in the DB for each node in the greaph
    for i in graph_nodes:
        # print(i)
        for j in range(0, max_phase+1):
            parent = exe_fetchone(cursor, f"select parent from graph_phase where node_id = {i} and phase = {j}")[0]
            G.nodes[i][j] = parent
    
    try:
        with open(f"{name}.csv", 'w') as csvfile:
            columns = ['x','y','osmid']
            for k in range(0, max_phase + 1):
                columns.append(k)
            writer = csv.DictWriter(csvfile, fieldnames=columns, extrasaction='ignore')
            writer.writeheader()
            for data in G.nodes(data=True):
                writer.writerow(data[1])
    except IOError:
        print("I/O error")
    
    # # assigns colors based on phase 4 parent (a default)
    # nc = ox.plot.get_node_colors_by_attr(G,attr=4)

    # # graphs
    # fig2, ax2 = ox.plot_graph(G, figsize=(10,10), node_size=10, node_zorder=2, node_color=nc)

con.close()


# get edge info
# select min(fromphase.phase) as joinphase, edge.* from edge join graph_phase as fromphase on edge.from = fromphase.node_id join graph_phase as tophase on edge.to = tophase.node_id and tophase.phase =fromphase.phase where fromphase.parent = tophase.parent group by edge.id order by joinphase desc, edge.length desc; 

# see the traversal 
# select count(*), parent, phase from graph_phase where traversed group by parent, phase order by phase desc , parent;

#analysis
# select distinct parent, phase from graph_phase order by parent, phase;

# select min(fromphase.phase) as joinphase, edge.* from edge join graph_phase as fromphase on edge.from = fromphase.node_id join graph_phase as tophase on edge.to = tophase.node_id and tophase.phase =fromphase.phase where fromphase.parent = tophase.parent group by edge.id order by joinphase desc, edge.length desc;


# next try graph_from_place for jefferson county ny
            # select edge.id, fromphase.parent, tophase.parent, edge.length * least(fromnetwork.sum_length,  tonetwork.sum_length) as gateway_size, count(combine_edges.id) from edge
            # join node as "from" on edge.from = "from".id
            # join node as "to" on edge.to = "to".id
            # join graph_phase as fromphase on "from".id = fromphase.node_id
            # join graph_phase as tophase on "to".id = tophase.node_id and fromphase.phase = tophase.phase 
            # join edge as combine_edges on combine_edges.from in fromphase.node_id or combine_edges.from in tophase.node_id or combine_edges.to in fromphase.node_id or combine_edges.to in tophase.node_id
            # join network_size as fromnetwork on fromnetwork.parent = fromphase.parent
            # join network_size as tonetwork on tonetwork.parent = tophase.parent
            # and fromphase.traversed = tophase.traversed
            # where fromphase.parent <> tophase.parent 
            # and fromphase.phase={ph}
            # and fromphase.traversed = false
            # group by edge.id
            # order by gateway_size;

# for i in edgescore:
#     G[i[1]][i[2]][0]['color'] = i[0]

# max_phase = exe_fetchone(cursor, "select max(phase) from graph_phase")[0]

# delete from node;

# select count(*), phase from graph_phase where not traversed and phase = (select max(phase) from graph_phase) group by phase;

