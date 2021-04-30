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
from math import log
import inquirer
import glob
import re

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

con.create_function("power", 2, lambda x, y: x**y)
con.create_function("log", 1, lambda x: log(x,10))

filenames = glob.glob('./*.json')
filenames.sort()


allRoadsQ = [
    inquirer.Confirm('roads', message="Would you like to include a fine variety of roads in your query?", default=False)
]

jsonQ = [
    inquirer.Confirm('json', message="Would you like to query from GeoJSON?", default=True),
]

fileQ = [    inquirer.List('file', message="Which file would you like to use", choices=filenames)]

selectRoadsQ = [
    inquirer.Confirm('highway', message="Would you like to include highways?", default=True),
    inquirer.List('pst', message="Which classes of roads would you like to include down to?", choices=['primary','secondary','tertiary','none'])
    ]

geographyQ = [
    inquirer.Text('geog',message="Enter your desired geography")
]

name = inquirer.prompt(geographyQ)['geog']

allRoads = inquirer.prompt(allRoadsQ)

if(not allRoads['roads']):
    
    pstQuery = {}
    pstQuery['none'] = ''
    pstQuery['primary'] = 'primary'
    pstQuery['secondary'] = pstQuery['primary'] + '|secondary'
    pstQuery['tertiary'] = pstQuery['secondary'] + '|tertiary'

    '["highway"~"motorway|trunk|primary|secondary|tertiary"]'
    selectRoads = inquirer.prompt(selectRoadsQ)
    separator = '|' if selectRoads['highway'] and selectRoads['pst'] != 'none' else ''
    highway = 'motorway|trunk' if selectRoads['highway'] else ''
    # print(selectRoads)
    cf = f"""["highway"~"{highway}{separator}{pstQuery[selectRoads['pst']]}"]"""
    settings = {"custom": cf}
    # G = ox.get_undirected(ox.graph_from_place(name, custom_filter=cf, retain_all=True))
else:
    vFineQ = [inquirer.Confirm('vfine', message="Would you like to include a Very Fine variety of roads?", default=False)]
    vFine = inquirer.prompt(vFineQ)['vfine']
    if vFine:
        settings = {"custom": '["highway"]["area"!~"yes"]["highway"!~"corridor|elevator|escalator|proposed|construction|bridleway|abandoned|platform|raceway"]["service"!~"parking|parking_aisle|driveway|emergency_access"]'}
    else:
        settings = {"custom": '["highway"]["area"!~"yes"]["highway"!~"cycleway|footway|path|steps|track|corridor|elevator|escalator|proposed|construction|bridleway|abandoned|platform|raceway"]["motor_vehicle"!~"no"]["motorcar"!~"no"]["service"!~"parking|parking_aisle|driveway|emergency_access"]'}
    # G = ox.get_undirected(ox.graph_from_place(name, network_type='drive', retain_all=True))

jsonAns = inquirer.prompt(jsonQ)
settings['json'] = jsonAns['json'] # having the settings dict is a bit sloppy if i only need one item from it. the json item isnt used.
print(jsonAns)
if (jsonAns['json']):
    fileAns = inquirer.prompt(fileQ)
    with open(fileAns['file']) as f:
        geojson = json.load(f)


        # NOTE: buffer(0) is a trick for fixing scenarios where polygons have overlapping coordinates 
    polygon = Polygon(shape(geojson['geometry']).buffer(0))
    download = datetime.now()
    print('download', download)
    G = ox.get_undirected(ox.graph_from_polygon(polygon,network_type='drive',custom_filter=settings['custom'], retain_all=True))
else:
    networkQ = [
        inquirer.Confirm('network', message="Would you like to query from a specified distance?", default=False),
    ]
    metersQ =[
        inquirer.Text('meters', message="how many meters?",validate=lambda _, x: re.match('\d+', x)),
        inquirer.List('dist_type', message='which distance type', choices=['bbox','network'])
    ]
    networkAns = inquirer.prompt(networkQ)
    if(networkAns['network']):
        metersAns = inquirer.prompt(metersQ)
        meters = int(metersAns['meters'])
        dist = metersAns['dist_type']
        download = datetime.now()
        print('download', download)
        G = ox.get_undirected(ox.graph_from_point(ox.geocode(name),network_type='drive',dist=meters,dist_type=dist,custom_filter=settings['custom'], retain_all=True)) #try network_type='all'
    else:
        download = datetime.now()
        print('download', download)
        G = ox.get_undirected(ox.graph_from_place(name,network_type='drive',custom_filter=settings['custom'], retain_all=True)) #try network_type='all'



### These comments will help me figure out how to prompt for filenames by searching the filesystem

# # https://medium.com/@pramukta/recipe-importing-geojson-into-shapely-da1edf79f41d
# with open("shape/north-jersey/commnor.geojsonl.json") as f:
#   geojson = json.load(f)


# # NOTE: buffer(0) is a trick for fixing scenarios where polygons have overlapping coordinates 
# polygon = Polygon(shape(geojson['geometry']).buffer(0)) 


# # G = ox.get_undirected(ox.graph_from_polygon(polygon,custom_filter='["highway"~"motorway|primary|trunk|secondary"]',retain_all=True))
# G = ox.get_undirected(ox.graph_from_polygon(polygon,network_type='drive',retain_all=True))

print("processing has begun",f"nodes: {G.number_of_nodes()}", f"edges: {G.number_of_edges()}")
beginning = datetime.now()
print(f"download time: {beginning - download}")
# imports the graph into the databate and processes the graph
with con:
    cursor = con.cursor()

    cursor.executescript("""
        drop table if exists node;
        create table node
        (
            id bigint not null,
            lat double precision,
            lon double precision,
            district bigint,
            constraint node_pkey
                primary key (id)
        );

        create index node_id_idx
            on node (id);

        drop table if exists candidate_edge;
        create table candidate_edge
        (
            fromparent bigint,
            toparent bigint,
            gateway_size double precision,
            phase integer,
            constraint candidate_edge_fromparent_fkey
                foreign key (fromparent) references node(id)
                    on update cascade on delete cascade,
            constraint candidate_edge_toparent_fkey
                foreign key (toparent) references node(id)
                    on update cascade on delete cascade
        );

        create index candidate_edge_gateway_size_idx
            on candidate_edge (gateway_size);

        create index candidate_edge_fromparent_idx
            on candidate_edge (fromparent);

        create index candidate_edge_toparent_idx
            on candidate_edge (toparent);

        create index candidate_edge_phase_index
            on candidate_edge (phase);

        create index candidate_edge_phase_gateway_size_index
            on candidate_edge (phase, gateway_size);

        drop table if exists edge;
        create table edge
        (
            "from" bigint,
            "to" bigint,
            length double precision,
            constraint edge_from_fkey
                foreign key ("from") references node(id)
                    on update cascade on delete cascade,
            constraint edge_to_fkey
                foreign key ("to") references node(id)
                    on update cascade on delete cascade
        );

        create index edge_length_idx
            on edge (length);

        create index edge_from_idx
            on edge ("from");

        create index edge_to_idx
            on edge ("to");

        drop table if exists graph_phase;
        create table graph_phase
        (
            phase integer not null,
            node_id bigint not null,
            parent bigint,
            traversed boolean default false,
            constraint graph_phase_unique
                unique(phase, node_id),
            constraint graph_phase_node_id_fkey
                foreign key (node_id) references node
                    on update cascade on delete cascade,
            constraint graph_phase_parent_fkey
                foreign key (parent) references node
                    on update cascade on delete cascade
        );

        create index phase_idx
            on graph_phase (phase);

        create index graph_phase_parent_idx
            on graph_phase (parent);

        create index graph_phase_node_id_idx
            on graph_phase (node_id);

        drop table if exists network_size;
        create table network_size
        (
            parent bigint not null,
            sum_length double precision,
            phase integer,
            constraint network_size_unique
                unique (parent, phase),
            constraint network_size_parent_fkey
                foreign key (parent) references node
                    on update cascade on delete cascade
        );

        create index network_size_sum_length_idx
            on network_size (sum_length);

        create index network_size_parent_idx
            on network_size (parent);

        create index network_size_phase_index
            on network_size (phase);
    """)

    #For each node, inserts into the "node" table.
    #The "node" table has "id", "lat", and "lon" columns
    # with sqlite3: cursor.executemany instead of p2.extras.e_v(cursor,), where values is (?,?,?)
    cursor.executemany(
        'INSERT INTO node(id, lat, lon) VALUES (?,?,?);',((
        n,
        data['y'],
        data['x']
    ) for n, data, in G.nodes(data=True)))

    #For each node, inserts the node with itself as its parent and 0 as its phase into the "graph_phase" table
    #The "graph_phase" table has the columns "phase", "node_id", "parent", and "traversed"
    #Through the process of this script, sets of nodes (i.e. subgraphs) with different parents in one phace will receive different parents in the next phase until it is not possible to continue this operation.
    cursor.executemany(
        'INSERT INTO graph_phase(phase, node_id, parent) VALUES (?,?,?);',((
        0,
        n,
        n
    ) for n, data, in G.nodes(data=True)))

    #For each edge, inserts "from" node, "to" node, and edge "length"
    cursor.executemany(
        'INSERT INTO edge("from", "to", length) VALUES (?,?,?);',((
        u,
        v,
        data['length']
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
            select fromphase.parent, tophase.parent from edge 
            join node as "from" on edge."from" = "from".id
            join node as "to" on edge."to" = "to".id
            join graph_phase as fromphase on "from".id = fromphase.node_id
            join graph_phase as tophase on "to".id = tophase.node_id and fromphase.phase = tophase.phase
            where fromphase.parent <> tophase.parent 
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
            INSERT INTO graph_phase("phase", "node_id", "parent")
            select {ph}, node_id, parent from graph_phase where phase = {ph - 1};
        """)
        print(f"Phase {ph}")

        #network size stores the length of subgraphs used in this algorithm. 
        cursor.execute(
            f"""
            insert into network_size 
            select graph_phase.parent, sum(edge.length) as sum_length, graph_phase.phase 
            from graph_phase 
            join edge on graph_phase.node_id = edge."from" 
            or graph_phase.node_id = edge."to" 
            where graph_phase.phase={ph} 
            group by graph_phase.parent, graph_phase.phase;
            """
        )
        
        # #don't think this is necessary
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
        cursor.execute(f"""
        insert into candidate_edge(gateway_size, fromparent, toparent, phase) 
        select ((1.0/sum(1.0/(edge.length + .01))) * min(fromnetwork.sum_length,  tonetwork.sum_length)) as gateway_size, fromphase.parent, tophase.parent, {ph} from edge
        join graph_phase as fromphase on edge."from" = fromphase.node_id
        join graph_phase as tophase on edge."to" = tophase.node_id and fromphase.phase = tophase.phase
        join network_size as fromnetwork on fromnetwork.parent = fromphase.parent and fromnetwork.phase = fromphase.phase
        join network_size as tonetwork on tonetwork.parent = tophase.parent and tonetwork.phase = tophase.phase
        where fromphase.parent <> tophase.parent
        and fromphase.phase={ph}
        group by fromphase.parent, tophase.parent, fromnetwork.sum_length, tonetwork.sum_length
        order by gateway_size;
        """)
        #probably don't need orderby, but it might help the indexing ^^

        #deletes old candidates
        # cursor.execute("delete from candidate_edge;")

        #inserts new candidates(no longer necessary because execute above)
        # psycopg2.extras.execute_values(cursor, """
        #     INSERT INTO candidate_edge VALUES %s on conflict(edge_id) do update set fromparent=excluded.fromparent, toparent=excluded.toparent, gateway_size=excluded.gateway_size;
        # """, candidates)

        # had the same insert network statement twice lol


        while(True):
            #the algorithm described above is executed here
            cursor.execute(f"""
            select candidate_edge.fromparent, candidate_edge.toparent, candidate_edge.gateway_size from candidate_edge
            join graph_phase as fromphase on candidate_edge.fromparent = fromphase.node_id and candidate_edge.phase = fromphase.phase
            join graph_phase as tophase on candidate_edge.toparent = tophase.node_id and tophase.phase = fromphase.phase
            where fromphase.phase = {ph}
            and not fromphase.traversed
            and not tophase.traversed
            order by candidate_edge.gateway_size
            limit 1;
            """)
            # combine_edges.from <> combine_edges.to prevents culdesacs from messing the procedure up

            #zero represents the node that will join two subgraphs together.
            zero = cursor.fetchone() #could be done by exefetch one but whatever
            print("zero", zero, 'not zero', not zero)

            #if there is no node that can join subgraphs together, this will not execute.
            if(not zero):
                break
            
            # prints nodes that are updated
            cursor.execute(f"""
            update graph_phase set parent = {min(zero[0],zero[1])}, traversed = true where parent in ({zero[0]},{zero[1]}) and phase = {ph};
            """)
            print("phase", ph)
        rounds.append(datetime.now()-phasebegin)
    
    for idx, val in enumerate(rounds):
        print(idx+1, val)

    phases = str(len(rounds) + 1) + " phases"
    nedges = f"nodes: {G.number_of_nodes()} edges: {G.number_of_edges()}"
    process="processing complete: HMS= " + str(datetime.now() - beginning)
    download=f"download time: {beginning - download}"
    print(nedges)
    print(process)
    print(download)

    # mycolors = []
    # graph_edges = G.edges
    # for i in graph_edges:
    #     G[i[0]][i[1]][i[2]]['color'] = get_first(cursor, exe_fetchone(cursor, f"select min(fromphase.phase) from edge join graph_phase as fromphase on edge.from = fromphase.node_id join graph_phase as tophase on edge.to = tophase.node_id and tophase.phase =fromphase.phase where fromphase.parent = tophase.parent and edge.from = {i[0]} and edge.to = {i[1]} group by edge.id;"))
        # mycolors.append(G[i[0]][i[1]][i[2]]['color'])

    # ec = ox.plot.get_edge_colors_by_attr(G, attr='color')


    districting = datetime.now()
    graph_nodes = G.nodes
    max_phase = exe_fetchone(cursor, "select max(phase) from graph_phase")[0]
    # adds parent properties from the "graph_nodes" table in the DB for each node in the greaph
    for i in graph_nodes:
        # print(i)
        phase = exe_fetch(cursor, f"select parent from graph_phase where node_id = {i} order by phase desc")
        district = 1
        for p in range(len(phase) - 1):
            district *= 2
            if(phase[p][0]!=phase[p+1][0]): #index 0 is the only index, representing parent
                district+=1
        cursor.execute(f"update node set district = {district} where id = {i}")
        for j in range(0, max_phase+1):
            parent = exe_fetchone(cursor, f"select parent from graph_phase where node_id = {i} and phase = {j}")[0]
            G.nodes[i][j] = parent
    
    dandp= f"districting and phasing: {datetime.now() - districting}"
    largest = exe_fetchone(cursor, f"select parent, count(*) nodes from graph_phase where phase = {len(rounds)} group by parent order by nodes desc")[1]
    print(largest, "the largest")
    print(dandp)
    

    # for row in exe_fetch(cursor, "select id from node"):
        # id = row["id"]
        
    
    try:
        print('exporting to csv')
        csv_name = f"{name}.csv"
        with open(csv_name, 'w') as csvfile:
            columns = ['x','y','osmid']
            for k in range(0, max_phase + 1):
                columns.append(k)
            writer = csv.DictWriter(csvfile, fieldnames=columns, extrasaction='ignore')
            writer.writeheader()
            for data in G.nodes(data=True):
                writer.writerow(data[1])
        print('creating sql dump')
        # https://stackoverflow.com/a/24106471
        sql_name = f"{name}.sql"
        with open(sql_name, 'w') as sqldump:
            for line in con.iterdump():
                sqldump.write('%s\n' % line)
        with open(f"{name}.log", 'w') as log:
            loglist=[phases,nedges,process,download,dandp]
            for line in loglist:
                log.write('%s\n' % line)

    except IOError:
        print("I/O error")
    
    # # assigns colors based on phase 4 parent (a default)
    # nc = ox.plot.get_node_colors_by_attr(G,attr=4)

    # # graphs
    # fig2, ax2 = ox.plot_graph(G, figsize=(10,10), node_size=10, node_zorder=2, node_color=nc)

con.close()
print(csv_name, "exported")
print(sql_name, "exported")


