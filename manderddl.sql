create table node(
    id int primary key,
    lat float,
    lon float
);

create table edge(
    id int primary key,
    "from" int references node(id),
    "to" int references node(id),
    "length" float
);

CREATE INDEX edge_length_idx ON edge
(
    "length"
);

create table graph_phase(
    phase int,
    node_id int references node(id),
    parent int references node(id)
);

CREATE INDEX phase_idx ON graph_phase
(
    phase
);

