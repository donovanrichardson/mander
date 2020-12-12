drop table if exists node;
create table node
(
	id bigint not null,
	lat double precision,
	lon double precision,
	constraint node_pkey
		primary key (id)
);

select rowid, * from node;
insert into node values(3, 44, 45);

create index node_id_idx
	on node (id);

drop table if exists candidate_edge;
create table candidate_edge
(
	fromparent bigint,
	toparent bigint,
	gateway_size double precision,
	phase integer,
	constraint candidate_edge_unique
	    unique(fromparent,toparent,phase),
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
	constraint edge_unique
	    unique("from","to"),
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


