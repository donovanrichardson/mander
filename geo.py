import numpy as np
import pandas as pd
import osmnx as ox
import networkx as nx
from geopandas import gpd
from osmnx import graph_to_gdfs, gdfs_to_graph, save_and_show, get_paths_to_simplify
from shapely.geometry import Point, LineString, shape, MultiPoint, box, Polygon, MultiLineString, mapping
from shapely.ops import linemerge
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
# https://www.timlrx.com/2019/01/05/cleaning-openstreetmap-intersections-in-python/

address = '2700 Shattuck Ave, Berkeley, CA'
G = ox.graph_from_address(address, network_type='drive', distance=750)

# brew install spatialindex