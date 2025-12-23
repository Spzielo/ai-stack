--
-- PostgreSQL database dump
--

\restrict GBNSaomNEXPb2GdqMLxwIlcwLwEeCGIefiLLpGYglIHVTaaWcuFLTPfUzYD1uU1

-- Dumped from database version 16.11 (Debian 16.11-1.pgdg13+1)
-- Dumped by pg_dump version 16.11 (Debian 16.11-1.pgdg13+1)

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

--
-- Name: uuid-ossp; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA public;


--
-- Name: EXTENSION "uuid-ossp"; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION "uuid-ossp" IS 'generate universally unique identifiers (UUIDs)';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: captures; Type: TABLE; Schema: public; Owner: ai
--

CREATE TABLE public.captures (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    source text DEFAULT 'manual'::text NOT NULL,
    content text NOT NULL,
    meta jsonb DEFAULT '{}'::jsonb NOT NULL,
    status text DEFAULT 'inbox'::text NOT NULL
);


ALTER TABLE public.captures OWNER TO ai;

--
-- Name: logs; Type: TABLE; Schema: public; Owner: ai
--

CREATE TABLE public.logs (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    type text NOT NULL,
    payload jsonb NOT NULL
);


ALTER TABLE public.logs OWNER TO ai;

--
-- Name: notes; Type: TABLE; Schema: public; Owner: ai
--

CREATE TABLE public.notes (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    title text DEFAULT ''::text NOT NULL,
    content text NOT NULL,
    meta jsonb DEFAULT '{}'::jsonb NOT NULL
);


ALTER TABLE public.notes OWNER TO ai;

--
-- Name: tasks; Type: TABLE; Schema: public; Owner: ai
--

CREATE TABLE public.tasks (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    title text NOT NULL,
    description text DEFAULT ''::text NOT NULL,
    status text DEFAULT 'todo'::text NOT NULL,
    priority integer DEFAULT 2 NOT NULL,
    due_at timestamp with time zone,
    meta jsonb DEFAULT '{}'::jsonb NOT NULL
);


ALTER TABLE public.tasks OWNER TO ai;

--
-- Data for Name: captures; Type: TABLE DATA; Schema: public; Owner: ai
--

COPY public.captures (id, created_at, source, content, meta, status) FROM stdin;
d39e4fe8-7df7-4c78-8d85-86ac4e986c1d	2025-12-22 14:03:30.875761+00	api	First thought in the brain	{}	inbox
73fb26ab-1ca0-4496-a806-bebb0bc0fc4f	2025-12-22 14:06:26.47423+00	api	FastAPI capture check	{}	inbox
\.


--
-- Data for Name: logs; Type: TABLE DATA; Schema: public; Owner: ai
--

COPY public.logs (id, created_at, type, payload) FROM stdin;
\.


--
-- Data for Name: notes; Type: TABLE DATA; Schema: public; Owner: ai
--

COPY public.notes (id, created_at, title, content, meta) FROM stdin;
6952590a-d597-4b38-ba8d-28f1125ed126	2025-12-23 06:53:16.907172+00		Idea for a new app: Tinder for cats.	{}
d4cb4a80-5fc0-4ce3-b9b5-675a94c4484e	2025-12-23 06:53:19.88979+00		Plan a trip to Japan including flights and hotels	{}
4b94469a-7604-4859-bb7e-6beaf785d18a	2025-12-23 06:54:00.632387+00	Idea for a new app: Tinder for cats	Idea for a new app: Tinder for cats.	{}
dfefb2e0-8071-4639-93cb-460d633eb10c	2025-12-23 06:54:03.404552+00	Plan a trip to Japan including flights and hotels	Plan a trip to Japan including flights and hotels	{}
3d0016ee-a61c-4950-b464-9f1a15215d7c	2025-12-23 07:48:17.462346+00	Vault Security Code	The secret code for the vault is 998877.	{}
c2de41f5-35ae-4860-b634-cb75362de57b	2025-12-23 07:49:06.207433+00	Vault secret code: 998877	The secret code for the vault is 998877.	{}
\.


--
-- Data for Name: tasks; Type: TABLE DATA; Schema: public; Owner: ai
--

COPY public.tasks (id, created_at, updated_at, title, description, status, priority, due_at, meta) FROM stdin;
d8aecd51-0a93-4980-97f3-382054d65db3	2025-12-23 06:53:58.088516+00	2025-12-23 06:53:58.088516+00	Buy milk	Remember to buy milk tomorrow	todo	2	2023-10-20 00:00:00+00	{}
\.


--
-- Name: captures captures_pkey; Type: CONSTRAINT; Schema: public; Owner: ai
--

ALTER TABLE ONLY public.captures
    ADD CONSTRAINT captures_pkey PRIMARY KEY (id);


--
-- Name: logs logs_pkey; Type: CONSTRAINT; Schema: public; Owner: ai
--

ALTER TABLE ONLY public.logs
    ADD CONSTRAINT logs_pkey PRIMARY KEY (id);


--
-- Name: notes notes_pkey; Type: CONSTRAINT; Schema: public; Owner: ai
--

ALTER TABLE ONLY public.notes
    ADD CONSTRAINT notes_pkey PRIMARY KEY (id);


--
-- Name: tasks tasks_pkey; Type: CONSTRAINT; Schema: public; Owner: ai
--

ALTER TABLE ONLY public.tasks
    ADD CONSTRAINT tasks_pkey PRIMARY KEY (id);


--
-- PostgreSQL database dump complete
--

\unrestrict GBNSaomNEXPb2GdqMLxwIlcwLwEeCGIefiLLpGYglIHVTaaWcuFLTPfUzYD1uU1

