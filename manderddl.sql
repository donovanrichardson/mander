--
-- PostgreSQL database dump
--

-- Dumped from database version 12.4
-- Dumped by pg_dump version 12.4

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: edge; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.edge (
    "from" bigint,
    "to" bigint,
    length double precision,
    id integer NOT NULL
);


ALTER TABLE public.edge OWNER TO postgres;

--
-- Name: edge_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.edge_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.edge_id_seq OWNER TO postgres;

--
-- Name: edge_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.edge_id_seq OWNED BY public.edge.id;


--
-- Name: graph_phase; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.graph_phase (
    phase integer NOT NULL,
    node_id bigint NOT NULL,
    parent bigint,
    traversed boolean DEFAULT false
);


ALTER TABLE public.graph_phase OWNER TO postgres;

--
-- Name: network_size; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.network_size (
    parent bigint NOT NULL,
    sum_length double precision
);


ALTER TABLE public.network_size OWNER TO postgres;

--
-- Name: node; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.node (
    id bigint NOT NULL,
    lat double precision,
    lon double precision
);


ALTER TABLE public.node OWNER TO postgres;

--
-- Name: edge id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.edge ALTER COLUMN id SET DEFAULT nextval('public.edge_id_seq'::regclass);


--
-- Data for Name: edge; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.edge ("from", "to", length, id) FROM stdin;
\.


--
-- Data for Name: graph_phase; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.graph_phase (phase, node_id, parent, traversed) FROM stdin;
\.


--
-- Data for Name: network_size; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.network_size (parent, sum_length) FROM stdin;
\.


--
-- Data for Name: node; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.node (id, lat, lon) FROM stdin;
\.


--
-- Name: edge_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.edge_id_seq', 159254, true);


--
-- Name: edge edge_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.edge
    ADD CONSTRAINT edge_pkey PRIMARY KEY (id);


--
-- Name: graph_phase graph_phase_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.graph_phase
    ADD CONSTRAINT graph_phase_pkey PRIMARY KEY (phase, node_id);


--
-- Name: network_size network_size_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.network_size
    ADD CONSTRAINT network_size_pkey PRIMARY KEY (parent);


--
-- Name: node node_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.node
    ADD CONSTRAINT node_pkey PRIMARY KEY (id);


--
-- Name: edge_from_idx; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX edge_from_idx ON public.edge USING btree ("from");


--
-- Name: edge_length_idx; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX edge_length_idx ON public.edge USING btree (length);


--
-- Name: edge_to_idx; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX edge_to_idx ON public.edge USING btree ("to");


--
-- Name: network_size_sum_length_idx; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX network_size_sum_length_idx ON public.network_size USING btree (sum_length);


--
-- Name: phase_idx; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX phase_idx ON public.graph_phase USING btree (phase);


--
-- Name: edge edge_from_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.edge
    ADD CONSTRAINT edge_from_fkey FOREIGN KEY ("from") REFERENCES public.node(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: edge edge_to_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.edge
    ADD CONSTRAINT edge_to_fkey FOREIGN KEY ("to") REFERENCES public.node(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: graph_phase graph_phase_node_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.graph_phase
    ADD CONSTRAINT graph_phase_node_id_fkey FOREIGN KEY (node_id) REFERENCES public.node(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: graph_phase graph_phase_parent_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.graph_phase
    ADD CONSTRAINT graph_phase_parent_fkey FOREIGN KEY (parent) REFERENCES public.node(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: network_size network_size_parent_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.network_size
    ADD CONSTRAINT network_size_parent_fkey FOREIGN KEY (parent) REFERENCES public.node(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

