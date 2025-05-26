--
-- PostgreSQL database dump
--

-- Dumped from database version 14.17 (Homebrew)
-- Dumped by pg_dump version 14.17 (Homebrew)

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
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: Mario
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO "Mario";

--
-- Name: carousel_images; Type: TABLE; Schema: public; Owner: Mario
--

CREATE TABLE public.carousel_images (
    id integer NOT NULL,
    filename character varying(255) NOT NULL,
    title character varying(255),
    description text,
    "order" integer,
    is_active boolean,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.carousel_images OWNER TO "Mario";

--
-- Name: carousel_images_id_seq; Type: SEQUENCE; Schema: public; Owner: Mario
--

CREATE SEQUENCE public.carousel_images_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.carousel_images_id_seq OWNER TO "Mario";

--
-- Name: carousel_images_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: Mario
--

ALTER SEQUENCE public.carousel_images_id_seq OWNED BY public.carousel_images.id;


--
-- Name: carouselimage; Type: TABLE; Schema: public; Owner: Mario
--

CREATE TABLE public.carouselimage (
    filename character varying(255) NOT NULL,
    title character varying(255),
    description text,
    "order" integer,
    is_active boolean,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    id integer NOT NULL
);


ALTER TABLE public.carouselimage OWNER TO "Mario";

--
-- Name: carouselimage_id_seq; Type: SEQUENCE; Schema: public; Owner: Mario
--

CREATE SEQUENCE public.carouselimage_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.carouselimage_id_seq OWNER TO "Mario";

--
-- Name: carouselimage_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: Mario
--

ALTER SEQUENCE public.carouselimage_id_seq OWNED BY public.carouselimage.id;


--
-- Name: claude_prompt_log; Type: TABLE; Schema: public; Owner: Mario
--

CREATE TABLE public.claude_prompt_log (
    id integer NOT NULL,
    prompt_type character varying(50),
    "timestamp" timestamp without time zone,
    response_length integer,
    prompt_text text,
    response_text text,
    user_id integer
);


ALTER TABLE public.claude_prompt_log OWNER TO "Mario";

--
-- Name: claude_prompt_log_id_seq; Type: SEQUENCE; Schema: public; Owner: Mario
--

CREATE SEQUENCE public.claude_prompt_log_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.claude_prompt_log_id_seq OWNER TO "Mario";

--
-- Name: claude_prompt_log_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: Mario
--

ALTER SEQUENCE public.claude_prompt_log_id_seq OWNED BY public.claude_prompt_log.id;


--
-- Name: claudepromptlog; Type: TABLE; Schema: public; Owner: Mario
--

CREATE TABLE public.claudepromptlog (
    prompt_type character varying(50),
    prompt_text text,
    response_text text,
    user_id integer,
    "timestamp" timestamp without time zone,
    response_length integer,
    id integer NOT NULL
);


ALTER TABLE public.claudepromptlog OWNER TO "Mario";

--
-- Name: claudepromptlog_id_seq; Type: SEQUENCE; Schema: public; Owner: Mario
--

CREATE SEQUENCE public.claudepromptlog_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.claudepromptlog_id_seq OWNER TO "Mario";

--
-- Name: claudepromptlog_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: Mario
--

ALTER SEQUENCE public.claudepromptlog_id_seq OWNED BY public.claudepromptlog.id;


--
-- Name: image; Type: TABLE; Schema: public; Owner: Mario
--

CREATE TABLE public.image (
    filename character varying(255) NOT NULL,
    filepath character varying(500) NOT NULL,
    upload_date timestamp without time zone NOT NULL,
    user_id integer NOT NULL,
    id integer NOT NULL
);


ALTER TABLE public.image OWNER TO "Mario";

--
-- Name: image_id_seq; Type: SEQUENCE; Schema: public; Owner: Mario
--

CREATE SEQUENCE public.image_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.image_id_seq OWNER TO "Mario";

--
-- Name: image_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: Mario
--

ALTER SEQUENCE public.image_id_seq OWNED BY public.image.id;


--
-- Name: location; Type: TABLE; Schema: public; Owner: Mario
--

CREATE TABLE public.location (
    name character varying(120),
    latitude double precision,
    longitude double precision,
    radius double precision,
    is_active boolean,
    id integer NOT NULL
);


ALTER TABLE public.location OWNER TO "Mario";

--
-- Name: location_id_seq; Type: SEQUENCE; Schema: public; Owner: Mario
--

CREATE SEQUENCE public.location_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.location_id_seq OWNER TO "Mario";

--
-- Name: location_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: Mario
--

ALTER SEQUENCE public.location_id_seq OWNED BY public.location.id;


--
-- Name: locations; Type: TABLE; Schema: public; Owner: Mario
--

CREATE TABLE public.locations (
    id integer NOT NULL,
    name character varying(120),
    latitude double precision,
    longitude double precision,
    radius double precision,
    is_active boolean
);


ALTER TABLE public.locations OWNER TO "Mario";

--
-- Name: locations_id_seq; Type: SEQUENCE; Schema: public; Owner: Mario
--

CREATE SEQUENCE public.locations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.locations_id_seq OWNER TO "Mario";

--
-- Name: locations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: Mario
--

ALTER SEQUENCE public.locations_id_seq OWNED BY public.locations.id;


--
-- Name: registration_request; Type: TABLE; Schema: public; Owner: Mario
--

CREATE TABLE public.registration_request (
    id integer NOT NULL,
    email character varying(120) NOT NULL,
    status character varying(20),
    username character varying(80) NOT NULL,
    password_hash character varying(128),
    request_date timestamp without time zone
);


ALTER TABLE public.registration_request OWNER TO "Mario";

--
-- Name: registration_request_id_seq; Type: SEQUENCE; Schema: public; Owner: Mario
--

CREATE SEQUENCE public.registration_request_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.registration_request_id_seq OWNER TO "Mario";

--
-- Name: registration_request_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: Mario
--

ALTER SEQUENCE public.registration_request_id_seq OWNED BY public.registration_request.id;


--
-- Name: registrationrequest; Type: TABLE; Schema: public; Owner: Mario
--

CREATE TABLE public.registrationrequest (
    username character varying(80) NOT NULL,
    email character varying(120) NOT NULL,
    password_hash character varying(128),
    request_date timestamp without time zone,
    status character varying(20),
    id integer NOT NULL
);


ALTER TABLE public.registrationrequest OWNER TO "Mario";

--
-- Name: registrationrequest_id_seq; Type: SEQUENCE; Schema: public; Owner: Mario
--

CREATE SEQUENCE public.registrationrequest_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.registrationrequest_id_seq OWNER TO "Mario";

--
-- Name: registrationrequest_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: Mario
--

ALTER SEQUENCE public.registrationrequest_id_seq OWNED BY public.registrationrequest.id;


--
-- Name: user; Type: TABLE; Schema: public; Owner: Mario
--

CREATE TABLE public."user" (
    username character varying(80) NOT NULL,
    email character varying(120) NOT NULL,
    password_hash character varying(255),
    is_admin boolean,
    is_approved boolean,
    registration_date timestamp without time zone,
    is_active boolean,
    login_token character varying(100),
    token_expiry timestamp without time zone,
    newsletter_subscription boolean,
    id integer NOT NULL
);


ALTER TABLE public."user" OWNER TO "Mario";

--
-- Name: user_id_seq; Type: SEQUENCE; Schema: public; Owner: Mario
--

CREATE SEQUENCE public.user_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.user_id_seq OWNER TO "Mario";

--
-- Name: user_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: Mario
--

ALTER SEQUENCE public.user_id_seq OWNED BY public."user".id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: Mario
--

CREATE TABLE public.users (
    id integer NOT NULL,
    email character varying(120) NOT NULL,
    password_hash character varying(255),
    is_active boolean,
    is_approved boolean,
    is_admin boolean,
    login_token character varying(100),
    token_expiry timestamp without time zone,
    newsletter_subscription boolean,
    username character varying(80) NOT NULL,
    registration_date timestamp without time zone
);


ALTER TABLE public.users OWNER TO "Mario";

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: Mario
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.users_id_seq OWNER TO "Mario";

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: Mario
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: carousel_images id; Type: DEFAULT; Schema: public; Owner: Mario
--

ALTER TABLE ONLY public.carousel_images ALTER COLUMN id SET DEFAULT nextval('public.carousel_images_id_seq'::regclass);


--
-- Name: carouselimage id; Type: DEFAULT; Schema: public; Owner: Mario
--

ALTER TABLE ONLY public.carouselimage ALTER COLUMN id SET DEFAULT nextval('public.carouselimage_id_seq'::regclass);


--
-- Name: claude_prompt_log id; Type: DEFAULT; Schema: public; Owner: Mario
--

ALTER TABLE ONLY public.claude_prompt_log ALTER COLUMN id SET DEFAULT nextval('public.claude_prompt_log_id_seq'::regclass);


--
-- Name: claudepromptlog id; Type: DEFAULT; Schema: public; Owner: Mario
--

ALTER TABLE ONLY public.claudepromptlog ALTER COLUMN id SET DEFAULT nextval('public.claudepromptlog_id_seq'::regclass);


--
-- Name: image id; Type: DEFAULT; Schema: public; Owner: Mario
--

ALTER TABLE ONLY public.image ALTER COLUMN id SET DEFAULT nextval('public.image_id_seq'::regclass);


--
-- Name: location id; Type: DEFAULT; Schema: public; Owner: Mario
--

ALTER TABLE ONLY public.location ALTER COLUMN id SET DEFAULT nextval('public.location_id_seq'::regclass);


--
-- Name: locations id; Type: DEFAULT; Schema: public; Owner: Mario
--

ALTER TABLE ONLY public.locations ALTER COLUMN id SET DEFAULT nextval('public.locations_id_seq'::regclass);


--
-- Name: registration_request id; Type: DEFAULT; Schema: public; Owner: Mario
--

ALTER TABLE ONLY public.registration_request ALTER COLUMN id SET DEFAULT nextval('public.registration_request_id_seq'::regclass);


--
-- Name: registrationrequest id; Type: DEFAULT; Schema: public; Owner: Mario
--

ALTER TABLE ONLY public.registrationrequest ALTER COLUMN id SET DEFAULT nextval('public.registrationrequest_id_seq'::regclass);


--
-- Name: user id; Type: DEFAULT; Schema: public; Owner: Mario
--

ALTER TABLE ONLY public."user" ALTER COLUMN id SET DEFAULT nextval('public.user_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: Mario
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: Mario
--

COPY public.alembic_version (version_num) FROM stdin;
6cd6c3b1984b
\.


--
-- Data for Name: carousel_images; Type: TABLE DATA; Schema: public; Owner: Mario
--

COPY public.carousel_images (id, filename, title, description, "order", is_active, created_at, updated_at) FROM stdin;
1	photo1.jpg	Bird Photo 1	Beautiful bird photo 1	1	t	2025-04-01 12:51:55.172791	2025-04-01 12:51:55.172796
2	photo10.jpeg	Bird Photo 2	Beautiful bird photo 2	2	t	2025-04-01 12:51:55.177553	2025-04-01 12:51:55.177556
3	photo11.jpeg	Bird Photo 3	Beautiful bird photo 3	3	t	2025-04-01 12:51:55.178235	2025-04-01 12:51:55.178237
4	photo12.jpeg	Bird Photo 4	Beautiful bird photo 4	4	t	2025-04-01 12:51:55.178811	2025-04-01 12:51:55.178813
5	photo13.jpeg	Bird Photo 5	Beautiful bird photo 5	5	t	2025-04-01 12:51:55.179505	2025-04-01 12:51:55.179507
6	photo14.jpg	Bird Photo 6	Beautiful bird photo 6	6	t	2025-04-01 12:51:55.180264	2025-04-01 12:51:55.180266
7	photo15.jpg	Bird Photo 7	Beautiful bird photo 7	7	t	2025-04-01 12:51:55.181003	2025-04-01 12:51:55.181005
8	photo16.jpeg	Bird Photo 8	Beautiful bird photo 8	8	t	2025-04-01 12:51:55.181734	2025-04-01 12:51:55.181736
9	photo17.jpeg	Bird Photo 9	Beautiful bird photo 9	9	t	2025-04-01 12:51:55.18246	2025-04-01 12:51:55.182461
10	photo18.jpeg	Bird Photo 10	Beautiful bird photo 10	10	t	2025-04-01 12:51:55.183188	2025-04-01 12:51:55.18319
11	photo19.jpeg	Bird Photo 11	Beautiful bird photo 11	11	t	2025-04-01 12:51:55.183919	2025-04-01 12:51:55.183921
12	photo2.jpeg	Bird Photo 12	Beautiful bird photo 12	12	t	2025-04-01 12:51:55.184844	2025-04-01 12:51:55.184845
13	photo20.jpeg	Bird Photo 13	Beautiful bird photo 13	13	t	2025-04-01 12:51:55.185648	2025-04-01 12:51:55.185649
14	photo3.jpeg	Bird Photo 14	Beautiful bird photo 14	14	t	2025-04-01 12:51:55.18647	2025-04-01 12:51:55.186472
15	photo4.jpeg	Bird Photo 15	Beautiful bird photo 15	15	t	2025-04-01 12:51:55.187448	2025-04-01 12:51:55.18745
16	photo5.jpeg	Bird Photo 16	Beautiful bird photo 16	16	t	2025-04-01 12:51:55.188214	2025-04-01 12:51:55.188217
17	photo6.jpeg	Bird Photo 17	Beautiful bird photo 17	17	t	2025-04-01 12:51:55.188845	2025-04-01 12:51:55.188847
18	photo7.jpeg	Bird Photo 18	Beautiful bird photo 18	18	t	2025-04-01 12:51:55.189455	2025-04-01 12:51:55.189457
19	photo8.jpeg	Bird Photo 19	Beautiful bird photo 19	19	t	2025-04-01 12:51:55.190028	2025-04-01 12:51:55.19003
20	photo9.jpeg	Bird Photo 20	Beautiful bird photo 20	20	t	2025-04-01 12:51:55.190544	2025-04-01 12:51:55.190545
\.


--
-- Data for Name: carouselimage; Type: TABLE DATA; Schema: public; Owner: Mario
--

COPY public.carouselimage (filename, title, description, "order", is_active, created_at, updated_at, id) FROM stdin;
\.


--
-- Data for Name: claude_prompt_log; Type: TABLE DATA; Schema: public; Owner: Mario
--

COPY public.claude_prompt_log (id, prompt_type, "timestamp", response_length, prompt_text, response_text, user_id) FROM stdin;
\.


--
-- Data for Name: claudepromptlog; Type: TABLE DATA; Schema: public; Owner: Mario
--

COPY public.claudepromptlog (prompt_type, prompt_text, response_text, user_id, "timestamp", response_length, id) FROM stdin;
\.


--
-- Data for Name: image; Type: TABLE DATA; Schema: public; Owner: Mario
--

COPY public.image (filename, filepath, upload_date, user_id, id) FROM stdin;
\.


--
-- Data for Name: location; Type: TABLE DATA; Schema: public; Owner: Mario
--

COPY public.location (name, latitude, longitude, radius, is_active, id) FROM stdin;
\.


--
-- Data for Name: locations; Type: TABLE DATA; Schema: public; Owner: Mario
--

COPY public.locations (id, name, latitude, longitude, radius, is_active) FROM stdin;
\.


--
-- Data for Name: registration_request; Type: TABLE DATA; Schema: public; Owner: Mario
--

COPY public.registration_request (id, email, status, username, password_hash, request_date) FROM stdin;
\.


--
-- Data for Name: registrationrequest; Type: TABLE DATA; Schema: public; Owner: Mario
--

COPY public.registrationrequest (username, email, password_hash, request_date, status, id) FROM stdin;
\.


--
-- Data for Name: user; Type: TABLE DATA; Schema: public; Owner: Mario
--

COPY public."user" (username, email, password_hash, is_admin, is_approved, registration_date, is_active, login_token, token_expiry, newsletter_subscription, id) FROM stdin;
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: Mario
--

COPY public.users (id, email, password_hash, is_active, is_approved, is_admin, login_token, token_expiry, newsletter_subscription, username, registration_date) FROM stdin;
1	alonsoencinci@gmail.com	scrypt:32768:8:1$I4QsUKywSDTwQ3eW$e9b74d0e31fd0739ee23bfe09a1ebf42367b47ddc41357d7f0bd5fa72676d3e27d3a54fed5b1881eee214c540102798cfeecfbc66f1c471d3f14849c325fc35d	t	f	t	\N	\N	t	alonsoencinci	2025-04-02 15:17:59.146554
2	sasandrap@gmail.com	scrypt:32768:8:1$9vhNgaAb5d5MKDmH$33c59202c329f50a3cc1da7ff90b942792d8497504166a3e010e9dcec4cea8c464463e02d136ade2ec5903ba53208d5f249bc9d5973f7de2dd099b9491802edd	t	f	f	\N	\N	t	sasandrap	2025-04-02 15:17:59.146554
3	jalonso91@gmail.com	scrypt:32768:8:1$YpMwLCGGoxeJQudL$b4dcda7b4286e2d2b17a236ded5179a606b61de79351f1f1f4ef807929e8cb4bd02f11b2899caa2abab57fd4998ba295f1f019314f4434fe671cb759cb007db5	t	f	f	\N	\N	t	jalonso91	2025-04-02 15:17:59.146554
4	nunualonso96@gmail.com	scrypt:32768:8:1$40xyBpGwNxW9WTS2$3de5caf7d0a6d7d0743dc4482d74a454f253b242baf295f78ecd5a987152b6632768326d6b9760bdc08dba5bef992ac74007ab1d3997efea2c55ba3141b9d82e	t	f	f	\N	\N	t	nunualonso96	2025-04-02 15:17:59.146554
\.


--
-- Name: carousel_images_id_seq; Type: SEQUENCE SET; Schema: public; Owner: Mario
--

SELECT pg_catalog.setval('public.carousel_images_id_seq', 20, true);


--
-- Name: carouselimage_id_seq; Type: SEQUENCE SET; Schema: public; Owner: Mario
--

SELECT pg_catalog.setval('public.carouselimage_id_seq', 1, false);


--
-- Name: claude_prompt_log_id_seq; Type: SEQUENCE SET; Schema: public; Owner: Mario
--

SELECT pg_catalog.setval('public.claude_prompt_log_id_seq', 1, false);


--
-- Name: claudepromptlog_id_seq; Type: SEQUENCE SET; Schema: public; Owner: Mario
--

SELECT pg_catalog.setval('public.claudepromptlog_id_seq', 1, false);


--
-- Name: image_id_seq; Type: SEQUENCE SET; Schema: public; Owner: Mario
--

SELECT pg_catalog.setval('public.image_id_seq', 1, false);


--
-- Name: location_id_seq; Type: SEQUENCE SET; Schema: public; Owner: Mario
--

SELECT pg_catalog.setval('public.location_id_seq', 1, false);


--
-- Name: locations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: Mario
--

SELECT pg_catalog.setval('public.locations_id_seq', 1, false);


--
-- Name: registration_request_id_seq; Type: SEQUENCE SET; Schema: public; Owner: Mario
--

SELECT pg_catalog.setval('public.registration_request_id_seq', 1, false);


--
-- Name: registrationrequest_id_seq; Type: SEQUENCE SET; Schema: public; Owner: Mario
--

SELECT pg_catalog.setval('public.registrationrequest_id_seq', 1, false);


--
-- Name: user_id_seq; Type: SEQUENCE SET; Schema: public; Owner: Mario
--

SELECT pg_catalog.setval('public.user_id_seq', 1, false);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: Mario
--

SELECT pg_catalog.setval('public.users_id_seq', 4, true);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: Mario
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: carousel_images carousel_images_pkey; Type: CONSTRAINT; Schema: public; Owner: Mario
--

ALTER TABLE ONLY public.carousel_images
    ADD CONSTRAINT carousel_images_pkey PRIMARY KEY (id);


--
-- Name: carouselimage carouselimage_pkey; Type: CONSTRAINT; Schema: public; Owner: Mario
--

ALTER TABLE ONLY public.carouselimage
    ADD CONSTRAINT carouselimage_pkey PRIMARY KEY (id);


--
-- Name: claude_prompt_log claude_prompt_log_pkey; Type: CONSTRAINT; Schema: public; Owner: Mario
--

ALTER TABLE ONLY public.claude_prompt_log
    ADD CONSTRAINT claude_prompt_log_pkey PRIMARY KEY (id);


--
-- Name: claudepromptlog claudepromptlog_pkey; Type: CONSTRAINT; Schema: public; Owner: Mario
--

ALTER TABLE ONLY public.claudepromptlog
    ADD CONSTRAINT claudepromptlog_pkey PRIMARY KEY (id);


--
-- Name: image image_pkey; Type: CONSTRAINT; Schema: public; Owner: Mario
--

ALTER TABLE ONLY public.image
    ADD CONSTRAINT image_pkey PRIMARY KEY (id);


--
-- Name: location location_pkey; Type: CONSTRAINT; Schema: public; Owner: Mario
--

ALTER TABLE ONLY public.location
    ADD CONSTRAINT location_pkey PRIMARY KEY (id);


--
-- Name: locations locations_pkey; Type: CONSTRAINT; Schema: public; Owner: Mario
--

ALTER TABLE ONLY public.locations
    ADD CONSTRAINT locations_pkey PRIMARY KEY (id);


--
-- Name: registration_request registration_request_email_key; Type: CONSTRAINT; Schema: public; Owner: Mario
--

ALTER TABLE ONLY public.registration_request
    ADD CONSTRAINT registration_request_email_key UNIQUE (email);


--
-- Name: registration_request registration_request_pkey; Type: CONSTRAINT; Schema: public; Owner: Mario
--

ALTER TABLE ONLY public.registration_request
    ADD CONSTRAINT registration_request_pkey PRIMARY KEY (id);


--
-- Name: registration_request registration_request_username_key; Type: CONSTRAINT; Schema: public; Owner: Mario
--

ALTER TABLE ONLY public.registration_request
    ADD CONSTRAINT registration_request_username_key UNIQUE (username);


--
-- Name: registrationrequest registrationrequest_email_key; Type: CONSTRAINT; Schema: public; Owner: Mario
--

ALTER TABLE ONLY public.registrationrequest
    ADD CONSTRAINT registrationrequest_email_key UNIQUE (email);


--
-- Name: registrationrequest registrationrequest_pkey; Type: CONSTRAINT; Schema: public; Owner: Mario
--

ALTER TABLE ONLY public.registrationrequest
    ADD CONSTRAINT registrationrequest_pkey PRIMARY KEY (id);


--
-- Name: registrationrequest registrationrequest_username_key; Type: CONSTRAINT; Schema: public; Owner: Mario
--

ALTER TABLE ONLY public.registrationrequest
    ADD CONSTRAINT registrationrequest_username_key UNIQUE (username);


--
-- Name: users uq_users_username; Type: CONSTRAINT; Schema: public; Owner: Mario
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT uq_users_username UNIQUE (username);


--
-- Name: user user_email_key; Type: CONSTRAINT; Schema: public; Owner: Mario
--

ALTER TABLE ONLY public."user"
    ADD CONSTRAINT user_email_key UNIQUE (email);


--
-- Name: user user_login_token_key; Type: CONSTRAINT; Schema: public; Owner: Mario
--

ALTER TABLE ONLY public."user"
    ADD CONSTRAINT user_login_token_key UNIQUE (login_token);


--
-- Name: user user_pkey; Type: CONSTRAINT; Schema: public; Owner: Mario
--

ALTER TABLE ONLY public."user"
    ADD CONSTRAINT user_pkey PRIMARY KEY (id);


--
-- Name: user user_username_key; Type: CONSTRAINT; Schema: public; Owner: Mario
--

ALTER TABLE ONLY public."user"
    ADD CONSTRAINT user_username_key UNIQUE (username);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: Mario
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_login_token_key; Type: CONSTRAINT; Schema: public; Owner: Mario
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_login_token_key UNIQUE (login_token);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: Mario
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: claude_prompt_log claude_prompt_log_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: Mario
--

ALTER TABLE ONLY public.claude_prompt_log
    ADD CONSTRAINT claude_prompt_log_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: claudepromptlog claudepromptlog_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: Mario
--

ALTER TABLE ONLY public.claudepromptlog
    ADD CONSTRAINT claudepromptlog_user_id_fkey FOREIGN KEY (user_id) REFERENCES public."user"(id);


--
-- Name: image image_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: Mario
--

ALTER TABLE ONLY public.image
    ADD CONSTRAINT image_user_id_fkey FOREIGN KEY (user_id) REFERENCES public."user"(id);


--
-- PostgreSQL database dump complete
--

