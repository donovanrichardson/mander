import sqlite3
from db import con
import inquirer
import glob
from datetime import datetime
import math

filenames = glob.glob('./*.sql')
filenames.sort()

fileQ = [
    inquirer.List('file', message="Which sql file would you like to import", choices=filenames),
    inquirer.Confirm('new', message="Would you like new calc algo?", default=True)
]

answers = inquirer.prompt(fileQ)

the_file = open(answers['file'], 'r')

# a shortcut to execute a query and return all results
def exe_fetch(cursor, query):
    cursor.execute(query)
    return cursor.fetchall()

# a shortcut to execute a query and return all results
def exe_fetch_params(cursor, query, params):
    cursor.execute(query, params)
    return cursor.fetchall()

# a shortcut to execute a query and return first result
def exe_fetchone(cursor, query):
    cursor.execute(query)
    return cursor.fetchone()

with con:

    cursor = con.cursor()
    cursor.executescript(the_file.read())

    max_phase = exe_fetchone(cursor, f"select max(phase) from graph_phase")[0]
    largest_nodes = exe_fetchone(cursor, f"select parent, count(*) nodes from graph_phase where phase = {max_phase} group by parent order by nodes desc")
    largest_edges = exe_fetchone(cursor, f'select count(), sum(length*length)/sum(length), sum(length), avg(length) from (select distinct edge.* from edge join graph_phase on graph_phase.node_id = edge."to" or graph_phase.node_id = edge."from" where graph_phase.phase = {max_phase} and graph_phase.parent = {largest_nodes[0]})')

    num_largest_nodes = float(largest_nodes[1])
    num_largest_edges = float(largest_edges[0])

    community_size = 200
    community_ratio = community_size / num_largest_nodes
    edge_com_ratio = community_ratio * num_largest_edges
    average_edge = float(largest_edges[1])
    edge_com_size = average_edge * edge_com_ratio
    edge_size_ratio = edge_com_size / float(largest_edges[2])

    # total_size = float(exe_fetchone(cursor, f"select sum(length) from edge")[0])

    base = num_largest_nodes**(1/float(max_phase))
    print("base", base)
    print("max phase", max_phase)
    print("nodes in largest component", num_largest_nodes)
    print("edges in largest component", num_largest_edges)
    # print("community size", community_size)
    print("mean self-weighted edge length meters", average_edge)
    print("arithmetic mean edge length meters", float(largest_edges[3]))

    if(answers['new']):
        print('old community size', community_size)
        # print("edge community size", edge_com_ratio)
        print("average total edge length in community", edge_com_size)
        print("desired number of communities in new algo", 1/edge_size_ratio)
        community_size = num_largest_nodes * edge_size_ratio
        print('new community size', community_size)
    else:
        print('community size', community_size)
        print("desired number of communities in algo", num_largest_nodes/community_size)

    print("phases for community size:", math.log(community_size,base))