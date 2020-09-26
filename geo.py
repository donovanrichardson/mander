import numpy as np
import pandas as pd
import osmnx as ox
import networkx as nx
from geopandas import gpd
from osmnx import graph_to_gdfs, graph_from_gdfs
import psycopg2
import psycopg2.extras
from db import con

def exe_fetch(query):
    with con.cursor() as cursor:
        cursor.execute(query)
        return cursor.fetchall()

def exe_fetchone(query):
    with con.cursor() as cursor:
        cursor.execute(query)
        return cursor.fetchone()

# , save_and_show, get_paths_to_simplify
# from shapely.geometry import Point, LineString, shape, MultiPoint, box, Polygon, MultiLineString, mapping
# from shapely.ops import linemerge
# import matplotlib.pyplot as plt
# from matplotlib.collections import LineCollection
# https://www.timlrx.com/2019/01/05/cleaning-openstreetmap-intersections-in-python/

address = '731 Park Avenue, Huntington NY, 11743'
G = ox.get_undirected(ox.graph_from_address(address, network_type='drive', dist=3000, retain_all=True))

fig, ax = ox.plot_graph(G, figsize=(10,10), node_color='orange', node_size=30,
node_zorder=2, node_edgecolor='k')

# for u, v ,keys, data in G.edges(data=True, keys=True):

#     print(u,v,data['length'], data['osmid'])

# print (G.nodes())

# cur = con.cursor()

# for n, data, in G.nodes(data=True):
#     print(n, data)
#     cur.execute(f"insert into node (id, lat, lon) values ({n},{data['y']},{data['x']});")
#     cur.execute(f"insert into graph_phase (phase, node_id, parent) values ({0},{n},{n});")

# cur.close()
# con.close()

# for u, v ,keys, data in G.edges(data=True, keys=True):
#     print(u,v,data['length'], data['osmid'])
#     cur.execute(f"insert into")

# len(ox.get_undirected(G).edges())

# brew install spatialindex



with con.cursor() as cursor:
    psycopg2.extras.execute_values(cursor, """
        INSERT INTO node(id, lat, lon) VALUES %s;
    """, ((
        n,
        data['y'],
        data['x']
    ) for n, data, in G.nodes(data=True)))
    psycopg2.extras.execute_values(cursor, """
        INSERT INTO graph_phase(phase, node_id, parent) VALUES %s;
    """, ((
        0,
        n,
        n
    ) for n, data, in G.nodes(data=True)))
    psycopg2.extras.execute_values(cursor, """
        INSERT INTO edge("from", "to", length) VALUES %s;
    """, ((
        u,
        v,
        data['length']
    ) for u, v ,keys, data in G.edges(data=True, keys=True)))
    ph = 0
    while(len(exe_fetch(f"select distinct parent from graph_phase where phase = {ph}")) > 1):
        last = exe_fetch(f"select * from graph_phase where phase = {ph}")
        working = exe_fetch(f"""
            select edge.id, fromphase.parent, tophase.parent from edge 
            join node as "from" on edge.from = "from".id
            join node as "to" on edge.to = "to".id
            join graph_phase as fromphase on "from".id = fromphase.node_id
            join graph_phase as tophase on "to".id = tophase.node_id and fromphase.phase = tophase.phase
            where fromphase.parent <> tophase.parent 
            and fromphase.phase={ph} 
            and fromphase.traversed = false
            order by length;
            """) #left out the traversed part
        if(len(working) < 1):
            print("nowork")
            break
        ph = ph+1
        print(ph, len(working))
        psycopg2.extras.execute_values(cursor, """
            INSERT INTO graph_phase("phase", "node_id", "parent") VALUES %s;
        """, ((
            ph,
            phase[1],
            phase[2]
        ) for phase in last))
        print(f"Phase {ph}")

        while(True):

            cursor.execute(f"""
            select edge.id, fromphase.parent, tophase.parent from edge 
            join node as "from" on edge.from = "from".id
            join node as "to" on edge.to = "to".id
            join graph_phase as fromphase on "from".id = fromphase.node_id
            join graph_phase as tophase on "to".id = tophase.node_id and fromphase.phase = tophase.phase 
            and fromphase.traversed = tophase.traversed
            where fromphase.parent <> tophase.parent 
            and fromphase.phase={ph} 
            and fromphase.traversed = false
            order by length
            limit 1;
            """)
            zero = cursor.fetchone()

            if(not zero):
                break

            print(exe_fetch(f"""
            update graph_phase set parent = {min(zero[1],zero[2])}, traversed = true where parent in ({zero[1]},{zero[2]}) and phase = {ph} returning *;
            """))
# shortest = exe_fetch("""
# select edge.id, edge.from, edge.to from edge 
# join node as "from" on edge.from = "from".id
# join node as "to" on edge.to = "to".id
# join graph_phase as fromphase on "from".id = fromphase.node_id
# join graph_phase as tophase on "to".id = tophase.node_id and fromphase.phase = tophase.phase
# where fromphase.parent <> tophase.parent and fromphase.phase=1
# order by length
# limit 1;
# """)[0]

# print(exe_fetch(f"""
# update graph_phase set parent = {min(shortest[1],shortest[2])} where node_id in ({shortest[1]},{shortest[2]}) and phase = {1} returning *;
# """))

# with con.cursor() as cursor:
#     while(True):

        # cursor.execute("""
        # select edge.id, edge.from, edge.to from edge 
        # join node as "from" on edge.from = "from".id
        # join node as "to" on edge.to = "to".id
        # join graph_phase as fromphase on "from".id = fromphase.node_id
        # join graph_phase as tophase on "to".id = tophase.node_id and fromphase.phase = tophase.phase 
        # and fromphase.traversed = tophase.traversed
        # where fromphase.parent <> tophase.parent 
        # and fromphase.phase=1 
        # and fromphase.traversed = false
        # order by length
        # limit 1;
        # """)
        # zero = cursor.fetchone()

        # if(not zero):
        #     break

        # print(exe_fetch(f"""
        # update graph_phase set parent = {min(zero[1],zero[2])}, traversed = true where parent in ({zero[1]},{zero[2]}) and phase = {1} returning *;
        # """))


    # print(len(cursor.fetchall()))
    # cursor.execute(f"select * from graph_phase where phase = {ph}")
    # this phasecursor.fetchall())

con.close()

# get edge info
# select min(fromphase.phase) as joinphase, edge.* from edge join graph_phase as fromphase on edge.from = fromphase.node_id join graph_phase as tophase on edge.to = tophase.node_id and tophase.phase =fromphase.phase where fromphase.parent = tophase.parent group by edge.id order by joinphase desc, edge.length desc; 

# see the traversal 
# select count(*), parent, phase from graph_phase where traversed group by parent, phase order by phase desc , parent;

# next try graph_from_place for jefferson county ny