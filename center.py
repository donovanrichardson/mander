import sqlite3
from db import con
import inquirer
import glob



filenames = glob.glob('./*.sql')
filenames.sort()

fileQ = [inquirer.List('file', message="Which sql file would you like to import", choices=filenames)]



the_file = open(inquirer.prompt(fileQ)['file'], 'r')

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


# con.row_factory = sqlite3.Row

with con:
    cursor = con.cursor()

    # cursor.executescript(the_file.read())

    # p = exe_fetch_params(cursor, "select parent, count(*) as num, (select max(phase) from graph_phase) phase from graph_phase where phase = ?", (14,))

    # print(p)

    cursor.executescript(the_file.read())
    centers, number, phase = exe_fetch(cursor, "select parent, count(*) as num, (select max(phase) from graph_phase) phase  from graph_phase where phase = (select max(phase) from graph_phase) group by parent order by num desc")[0]
    # print(level, number, phase)
    distQ = [inquirer.Text('dist',message='enter the district', default=centers)]
    centers = inquirer.prompt(distQ)['dist']
    phases = list(map(lambda p: p[0],exe_fetch_params(cursor, "select distinct phase from graph_phase where parent = ? order by phase desc", [centers])))
    print(phases)
    phaseQ = [inquirer.List('phase',message='select the phase', choices=phases, default=phases[0])]
    phase = inquirer.prompt(phaseQ)['phase']
    centers = (centers,)

    while(phase >0):
        query = f"""
        select count(*) num_neighs, *, ? phase from
        (select distinct child.parent,
        coalesce((case when child.parent <> fromparent.parent then fromparent.parent else null end),
            (case when child.parent <> toparent.parent then toparent.parent else null end)) as neighbor
        from graph_phase
            join graph_phase as child on child.node_id = graph_phase.node_id
            join edge on edge."from" = child.node_id or edge."to" = child.node_id
            join graph_phase as fromparent on edge."from" = fromparent.node_id and child.phase = fromparent.phase
            join graph_phase as toparent on edge."to" = toparent.node_id and child.phase = toparent.phase
        where graph_phase.phase = ?
        and graph_phase.parent in ({','.join(centers)})
        and child.phase=? and neighbor not null)
            as temp group by parent order by num_neighs desc, parent;
        """
        print(phase)
        result = exe_fetch_params(cursor, query, (phase-1,phase,phase-1))
        centers = tuple(map(lambda j: str(j[1]), filter(lambda i: i[0] == result[0][0], result)))
        phase -=1
        
    print(centers[0])