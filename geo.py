import numpy as np
import pandas as pd
import osmnx as ox
import networkx as nx
from geopandas import gpd
from osmnx import graph_to_gdfs, graph_from_gdfs
# , save_and_show, get_paths_to_simplify
# from shapely.geometry import Point, LineString, shape, MultiPoint, box, Polygon, MultiLineString, mapping
# from shapely.ops import linemerge
# import matplotlib.pyplot as plt
# from matplotlib.collections import LineCollection
# https://www.timlrx.com/2019/01/05/cleaning-openstreetmap-intersections-in-python/

address = '731 Park Avenue, Huntington NY, 11743'
G = ox.get_undirected(ox.graph_from_address(address, network_type='drive', dist=750, retain_all=True))

# fig, ax = ox.plot_graph(G, figsize=(10,10), node_color='orange', node_size=30,
# node_zorder=2, node_edgecolor='k')

for u, v ,keys, data in G.edges(data=True, keys=True):

    print(u,v,data['length'], data['osmid'])

# len(ox.get_undirected(G).edges())

# brew install spatialindex