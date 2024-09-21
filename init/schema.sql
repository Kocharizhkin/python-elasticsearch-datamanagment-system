--
-- PostgreSQL database dump
--

-- Dumped from database version 15.4 (Ubuntu 15.4-1.pgdg22.04+1)
-- Dumped by pg_dump version 15.4 (Ubuntu 15.4-1.pgdg22.04+1)

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
-- Name: pg_trgm; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pg_trgm WITH SCHEMA public;


--
-- Name: EXTENSION pg_trgm; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION pg_trgm IS 'text similarity measurement and index searching based on trigrams';


--
-- Name: trigram_similarity(text, text); Type: FUNCTION; Schema: public; Owner: mkniga
--

CREATE FUNCTION public.trigram_similarity(text, text) RETURNS double precision
    LANGUAGE sql IMMUTABLE
    AS $_$
  SELECT similarity($1, $2);
$_$;


ALTER FUNCTION public.trigram_similarity(text, text) OWNER TO mkniga;

--
-- Name: update_tsvectors(); Type: FUNCTION; Schema: public; Owner: mkniga
--

CREATE FUNCTION public.update_tsvectors() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    BEGIN
        INSERT INTO book_tsvectors (book_id, tsv_isbn, tsv_author, tsv_title, tsv_publication_year, tsv_publisher, tsv_all)
        VALUES (
            NEW.id,
            to_tsvector('russian', coalesce(NEW.isbn, '')),
            to_tsvector('russian', coalesce(NEW.author, '')),
            to_tsvector('russian', coalesce(NEW.title, '')),
            to_tsvector('russian', coalesce(NEW.publication_year, '')),
            to_tsvector('russian', coalesce(NEW.publisher, '')),
            to_tsvector('russian', coalesce(NEW.isbn, '') || ' ' || coalesce(NEW.author, '') || ' ' || coalesce(NEW.title, '') || ' ' || coalesce(NEW.publication_year, '') || ' ' || coalesce(NEW.publisher, ''))
        )
        ON CONFLICT (book_id)
        DO UPDATE SET
            tsv_isbn = to_tsvector('russian', coalesce(NEW.isbn, '')),
            tsv_author = to_tsvector('russian', coalesce(NEW.author, '')),
            tsv_title = to_tsvector('russian', coalesce(NEW.title, '')),
            tsv_publication_year = to_tsvector('russian', coalesce(NEW.publication_year, '')),
            tsv_publisher = to_tsvector('russian', coalesce(NEW.publisher, '')),
            tsv_all = to_tsvector('russian', coalesce(NEW.isbn, '') || ' ' || coalesce(NEW.author, '') || ' ' || coalesce(NEW.title, '') || ' ' || coalesce(NEW.publication_year, '') || ' ' || coalesce(NEW.publisher, ''));
    EXCEPTION
        WHEN OTHERS THEN
            RAISE EXCEPTION 'Error updating tsvectors for book_id %: %', NEW.id, SQLERRM;
    END;
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.update_tsvectors() OWNER TO mkniga;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alpina; Type: TABLE; Schema: public; Owner: mkniga
--

CREATE TABLE public.alpina (
    id integer NOT NULL,
    update_date date,
    publication_year character varying(255),
    page_count character varying(255),
    weight double precision,
    supplier_price double precision,
    display_price double precision,
    delivery_timelines text,
    isbn character varying(255),
    dimensions character varying(255),
    author character varying(255),
    book_supplier character varying(255),
    title character varying(255),
    publisher character varying(255),
    cover text
);


ALTER TABLE public.alpina OWNER TO mkniga;

--
-- Name: alpina_id_seq; Type: SEQUENCE; Schema: public; Owner: mkniga
--

CREATE SEQUENCE public.alpina_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.alpina_id_seq OWNER TO mkniga;

--
-- Name: alpina_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: mkniga
--

ALTER SEQUENCE public.alpina_id_seq OWNED BY public.alpina.id;


--
-- Name: assorst; Type: TABLE; Schema: public; Owner: mkniga
--

CREATE TABLE public.assorst (
    id integer NOT NULL,
    update_date date,
    publication_year character varying(255),
    page_count character varying(255),
    weight double precision,
    supplier_price double precision,
    display_price double precision,
    delivery_timelines text,
    isbn character varying(255),
    dimensions character varying(255),
    author character varying(255),
    book_supplier character varying(255),
    title character varying(255),
    publisher character varying(255),
    cover text
);


ALTER TABLE public.assorst OWNER TO mkniga;

--
-- Name: assorst_id_seq; Type: SEQUENCE; Schema: public; Owner: mkniga
--

CREATE SEQUENCE public.assorst_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.assorst_id_seq OWNER TO mkniga;

--
-- Name: assorst_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: mkniga
--

ALTER SEQUENCE public.assorst_id_seq OWNED BY public.assorst.id;


--
-- Name: assort; Type: TABLE; Schema: public; Owner: mkniga
--

CREATE TABLE public.assort (
    id integer NOT NULL,
    update_date date,
    publication_year character varying(255),
    page_count character varying(255),
    weight double precision,
    supplier_price double precision,
    display_price double precision,
    delivery_timelines text,
    isbn character varying(255),
    dimensions character varying(255),
    author character varying(255),
    book_supplier character varying(255),
    title character varying(255),
    publisher character varying(255),
    cover text
);


ALTER TABLE public.assort OWNER TO mkniga;

--
-- Name: assort_id_seq; Type: SEQUENCE; Schema: public; Owner: mkniga
--

CREATE SEQUENCE public.assort_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.assort_id_seq OWNER TO mkniga;

--
-- Name: assort_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: mkniga
--

ALTER SEQUENCE public.assort_id_seq OWNED BY public.assort.id;


--
-- Name: ast_eksmo; Type: TABLE; Schema: public; Owner: mkniga
--

CREATE TABLE public.ast_eksmo (
    id integer NOT NULL,
    update_date date,
    publication_year character varying(255),
    page_count character varying(255),
    weight double precision,
    supplier_price double precision,
    display_price double precision,
    delivery_timelines text,
    isbn character varying(255),
    dimensions character varying(255),
    author character varying(255),
    book_supplier character varying(255),
    title character varying(255),
    publisher character varying(255),
    cover text
);


ALTER TABLE public.ast_eksmo OWNER TO mkniga;

--
-- Name: ast_eksmo_id_seq; Type: SEQUENCE; Schema: public; Owner: mkniga
--

CREATE SEQUENCE public.ast_eksmo_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.ast_eksmo_id_seq OWNER TO mkniga;

--
-- Name: ast_eksmo_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: mkniga
--

ALTER SEQUENCE public.ast_eksmo_id_seq OWNED BY public.ast_eksmo.id;


--
-- Name: azbuka_etc; Type: TABLE; Schema: public; Owner: mkniga
--

CREATE TABLE public.azbuka_etc (
    id integer NOT NULL,
    update_date date,
    publication_year character varying(255),
    page_count character varying(255),
    weight double precision,
    supplier_price double precision,
    display_price double precision,
    delivery_timelines text,
    isbn character varying(255),
    dimensions character varying(255),
    author character varying(255),
    book_supplier character varying(255),
    title character varying(255),
    publisher character varying(255),
    cover text
);


ALTER TABLE public.azbuka_etc OWNER TO mkniga;

--
-- Name: azbuka_etc_id_seq; Type: SEQUENCE; Schema: public; Owner: mkniga
--

CREATE SEQUENCE public.azbuka_etc_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.azbuka_etc_id_seq OWNER TO mkniga;

--
-- Name: azbuka_etc_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: mkniga
--

ALTER SEQUENCE public.azbuka_etc_id_seq OWNED BY public.azbuka_etc.id;


--
-- Name: book_tsvectors; Type: TABLE; Schema: public; Owner: mkniga
--

CREATE TABLE public.book_tsvectors (
    id integer NOT NULL,
    book_id integer,
    tsv_isbn tsvector,
    tsv_author tsvector,
    tsv_title tsvector,
    tsv_publication_year tsvector,
    tsv_publisher tsvector,
    tsv_all tsvector
);


ALTER TABLE public.book_tsvectors OWNER TO mkniga;

--
-- Name: book_tsvectors_id_seq; Type: SEQUENCE; Schema: public; Owner: mkniga
--

CREATE SEQUENCE public.book_tsvectors_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.book_tsvectors_id_seq OWNER TO mkniga;

--
-- Name: book_tsvectors_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: mkniga
--

ALTER SEQUENCE public.book_tsvectors_id_seq OWNED BY public.book_tsvectors.id;


--
-- Name: books; Type: TABLE; Schema: public; Owner: mkniga
--

CREATE TABLE public.books (
    id integer NOT NULL,
    isbn character varying,
    author character varying,
    title character varying,
    publication_year character varying,
    publisher character varying,
    alpina_id json,
    assorst_id json,
    polyandria_id json,
    azbuka_etc_id json,
    slowbooks_id json,
    omega_id json,
    ast_eksmo_id json,
    individuum_id json,
    mif_id json,
    limbakh_id json,
    supplier_36_6_id json,
    assort_id json,
    ts tsvector GENERATED ALWAYS AS (to_tsvector('russian'::regconfig, (((((((((isbn)::text || ' '::text) || (author)::text) || ' '::text) || (title)::text) || ' '::text) || (publication_year)::text) || ' '::text) || (publisher)::text))) STORED
);


ALTER TABLE public.books OWNER TO mkniga;

--
-- Name: books_id_seq; Type: SEQUENCE; Schema: public; Owner: mkniga
--

CREATE SEQUENCE public.books_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.books_id_seq OWNER TO mkniga;

--
-- Name: books_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: mkniga
--

ALTER SEQUENCE public.books_id_seq OWNED BY public.books.id;


--
-- Name: individuum; Type: TABLE; Schema: public; Owner: mkniga
--

CREATE TABLE public.individuum (
    id integer NOT NULL,
    update_date date,
    publication_year character varying(255),
    page_count character varying(255),
    weight double precision,
    supplier_price double precision,
    display_price double precision,
    delivery_timelines text,
    isbn character varying(255),
    dimensions character varying(255),
    author character varying(255),
    book_supplier character varying(255),
    title character varying(255),
    publisher character varying(255),
    cover text
);


ALTER TABLE public.individuum OWNER TO mkniga;

--
-- Name: individuum_id_seq; Type: SEQUENCE; Schema: public; Owner: mkniga
--

CREATE SEQUENCE public.individuum_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.individuum_id_seq OWNER TO mkniga;

--
-- Name: individuum_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: mkniga
--

ALTER SEQUENCE public.individuum_id_seq OWNED BY public.individuum.id;


--
-- Name: limbakh; Type: TABLE; Schema: public; Owner: mkniga
--

CREATE TABLE public.limbakh (
    id integer NOT NULL,
    update_date date,
    publication_year character varying(255),
    page_count character varying(255),
    weight double precision,
    supplier_price double precision,
    display_price double precision,
    delivery_timelines text,
    isbn character varying(255),
    dimensions character varying(255),
    author character varying(255),
    book_supplier character varying(255),
    title character varying(255),
    publisher character varying(255),
    cover text
);


ALTER TABLE public.limbakh OWNER TO mkniga;

--
-- Name: limbakh_id_seq; Type: SEQUENCE; Schema: public; Owner: mkniga
--

CREATE SEQUENCE public.limbakh_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.limbakh_id_seq OWNER TO mkniga;

--
-- Name: limbakh_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: mkniga
--

ALTER SEQUENCE public.limbakh_id_seq OWNED BY public.limbakh.id;


--
-- Name: mif; Type: TABLE; Schema: public; Owner: mkniga
--

CREATE TABLE public.mif (
    id integer NOT NULL,
    update_date date,
    publication_year character varying(255),
    page_count character varying(255),
    weight double precision,
    supplier_price double precision,
    display_price double precision,
    delivery_timelines text,
    isbn character varying(255),
    dimensions character varying(255),
    author character varying(255),
    book_supplier character varying(255),
    title character varying(255),
    publisher character varying(255),
    cover text
);


ALTER TABLE public.mif OWNER TO mkniga;

--
-- Name: mif_id_seq; Type: SEQUENCE; Schema: public; Owner: mkniga
--

CREATE SEQUENCE public.mif_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.mif_id_seq OWNER TO mkniga;

--
-- Name: mif_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: mkniga
--

ALTER SEQUENCE public.mif_id_seq OWNED BY public.mif.id;


--
-- Name: omega; Type: TABLE; Schema: public; Owner: mkniga
--

CREATE TABLE public.omega (
    id integer NOT NULL,
    update_date date,
    publication_year character varying(255),
    page_count character varying(255),
    weight double precision,
    supplier_price double precision,
    display_price double precision,
    delivery_timelines text,
    isbn character varying(255),
    dimensions character varying(255),
    author character varying(255),
    book_supplier character varying(255),
    title character varying(255),
    publisher character varying(255),
    cover text
);


ALTER TABLE public.omega OWNER TO mkniga;

--
-- Name: omega_id_seq; Type: SEQUENCE; Schema: public; Owner: mkniga
--

CREATE SEQUENCE public.omega_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.omega_id_seq OWNER TO mkniga;

--
-- Name: omega_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: mkniga
--

ALTER SEQUENCE public.omega_id_seq OWNED BY public.omega.id;


--
-- Name: polyandria; Type: TABLE; Schema: public; Owner: mkniga
--

CREATE TABLE public.polyandria (
    id integer NOT NULL,
    update_date date,
    publication_year character varying(255),
    page_count character varying(255),
    weight double precision,
    supplier_price double precision,
    display_price double precision,
    delivery_timelines text,
    isbn character varying(255),
    dimensions character varying(255),
    author character varying(255),
    book_supplier character varying(255),
    title character varying(255),
    publisher character varying(255),
    cover text
);


ALTER TABLE public.polyandria OWNER TO mkniga;

--
-- Name: polyandria_id_seq; Type: SEQUENCE; Schema: public; Owner: mkniga
--

CREATE SEQUENCE public.polyandria_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.polyandria_id_seq OWNER TO mkniga;

--
-- Name: polyandria_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: mkniga
--

ALTER SEQUENCE public.polyandria_id_seq OWNED BY public.polyandria.id;


--
-- Name: slowbooks; Type: TABLE; Schema: public; Owner: mkniga
--

CREATE TABLE public.slowbooks (
    id integer NOT NULL,
    update_date date,
    publication_year character varying(255),
    page_count character varying(255),
    weight double precision,
    supplier_price double precision,
    display_price double precision,
    delivery_timelines text,
    isbn character varying(255),
    dimensions character varying(255),
    author character varying(255),
    book_supplier character varying(255),
    title character varying(255),
    publisher character varying(255),
    cover text
);


ALTER TABLE public.slowbooks OWNER TO mkniga;

--
-- Name: slowbooks_id_seq; Type: SEQUENCE; Schema: public; Owner: mkniga
--

CREATE SEQUENCE public.slowbooks_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.slowbooks_id_seq OWNER TO mkniga;

--
-- Name: slowbooks_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: mkniga
--

ALTER SEQUENCE public.slowbooks_id_seq OWNED BY public.slowbooks.id;


--
-- Name: supplier_36_6; Type: TABLE; Schema: public; Owner: mkniga
--

CREATE TABLE public.supplier_36_6 (
    id integer NOT NULL,
    update_date date,
    publication_year character varying(255),
    page_count character varying(255),
    weight double precision,
    supplier_price double precision,
    display_price double precision,
    delivery_timelines text,
    isbn character varying(255),
    dimensions character varying(255),
    author character varying(255),
    book_supplier character varying(255),
    title character varying(255),
    publisher character varying(255),
    cover text
);


ALTER TABLE public.supplier_36_6 OWNER TO mkniga;

--
-- Name: supplier_36_6_id_seq; Type: SEQUENCE; Schema: public; Owner: mkniga
--

CREATE SEQUENCE public.supplier_36_6_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.supplier_36_6_id_seq OWNER TO mkniga;

--
-- Name: supplier_36_6_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: mkniga
--

ALTER SEQUENCE public.supplier_36_6_id_seq OWNED BY public.supplier_36_6.id;


--
-- Name: updates; Type: TABLE; Schema: public; Owner: mkniga
--

CREATE TABLE public.updates (
    id integer NOT NULL,
    current_sheet character varying(255),
    processed_rows integer,
    total_rows integer,
    update_start_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    time_total interval
);


ALTER TABLE public.updates OWNER TO mkniga;

--
-- Name: updates_id_seq; Type: SEQUENCE; Schema: public; Owner: mkniga
--

CREATE SEQUENCE public.updates_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.updates_id_seq OWNER TO mkniga;

--
-- Name: updates_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: mkniga
--

ALTER SEQUENCE public.updates_id_seq OWNED BY public.updates.id;


--
-- Name: alpina id; Type: DEFAULT; Schema: public; Owner: mkniga
--

ALTER TABLE ONLY public.alpina ALTER COLUMN id SET DEFAULT nextval('public.alpina_id_seq'::regclass);


--
-- Name: assorst id; Type: DEFAULT; Schema: public; Owner: mkniga
--

ALTER TABLE ONLY public.assorst ALTER COLUMN id SET DEFAULT nextval('public.assorst_id_seq'::regclass);


--
-- Name: assort id; Type: DEFAULT; Schema: public; Owner: mkniga
--

ALTER TABLE ONLY public.assort ALTER COLUMN id SET DEFAULT nextval('public.assort_id_seq'::regclass);


--
-- Name: ast_eksmo id; Type: DEFAULT; Schema: public; Owner: mkniga
--

ALTER TABLE ONLY public.ast_eksmo ALTER COLUMN id SET DEFAULT nextval('public.ast_eksmo_id_seq'::regclass);


--
-- Name: azbuka_etc id; Type: DEFAULT; Schema: public; Owner: mkniga
--

ALTER TABLE ONLY public.azbuka_etc ALTER COLUMN id SET DEFAULT nextval('public.azbuka_etc_id_seq'::regclass);


--
-- Name: book_tsvectors id; Type: DEFAULT; Schema: public; Owner: mkniga
--

ALTER TABLE ONLY public.book_tsvectors ALTER COLUMN id SET DEFAULT nextval('public.book_tsvectors_id_seq'::regclass);


--
-- Name: books id; Type: DEFAULT; Schema: public; Owner: mkniga
--

ALTER TABLE ONLY public.books ALTER COLUMN id SET DEFAULT nextval('public.books_id_seq'::regclass);


--
-- Name: individuum id; Type: DEFAULT; Schema: public; Owner: mkniga
--

ALTER TABLE ONLY public.individuum ALTER COLUMN id SET DEFAULT nextval('public.individuum_id_seq'::regclass);


--
-- Name: limbakh id; Type: DEFAULT; Schema: public; Owner: mkniga
--

ALTER TABLE ONLY public.limbakh ALTER COLUMN id SET DEFAULT nextval('public.limbakh_id_seq'::regclass);


--
-- Name: mif id; Type: DEFAULT; Schema: public; Owner: mkniga
--

ALTER TABLE ONLY public.mif ALTER COLUMN id SET DEFAULT nextval('public.mif_id_seq'::regclass);


--
-- Name: omega id; Type: DEFAULT; Schema: public; Owner: mkniga
--

ALTER TABLE ONLY public.omega ALTER COLUMN id SET DEFAULT nextval('public.omega_id_seq'::regclass);


--
-- Name: polyandria id; Type: DEFAULT; Schema: public; Owner: mkniga
--

ALTER TABLE ONLY public.polyandria ALTER COLUMN id SET DEFAULT nextval('public.polyandria_id_seq'::regclass);


--
-- Name: slowbooks id; Type: DEFAULT; Schema: public; Owner: mkniga
--

ALTER TABLE ONLY public.slowbooks ALTER COLUMN id SET DEFAULT nextval('public.slowbooks_id_seq'::regclass);


--
-- Name: supplier_36_6 id; Type: DEFAULT; Schema: public; Owner: mkniga
--

ALTER TABLE ONLY public.supplier_36_6 ALTER COLUMN id SET DEFAULT nextval('public.supplier_36_6_id_seq'::regclass);


--
-- Name: updates id; Type: DEFAULT; Schema: public; Owner: mkniga
--

ALTER TABLE ONLY public.updates ALTER COLUMN id SET DEFAULT nextval('public.updates_id_seq'::regclass);


--
-- Name: alpina alpina_pkey; Type: CONSTRAINT; Schema: public; Owner: mkniga
--

ALTER TABLE ONLY public.alpina
    ADD CONSTRAINT alpina_pkey PRIMARY KEY (id);


--
-- Name: assorst assorst_pkey; Type: CONSTRAINT; Schema: public; Owner: mkniga
--

ALTER TABLE ONLY public.assorst
    ADD CONSTRAINT assorst_pkey PRIMARY KEY (id);


--
-- Name: assort assort_pkey; Type: CONSTRAINT; Schema: public; Owner: mkniga
--

ALTER TABLE ONLY public.assort
    ADD CONSTRAINT assort_pkey PRIMARY KEY (id);


--
-- Name: ast_eksmo ast_eksmo_pkey; Type: CONSTRAINT; Schema: public; Owner: mkniga
--

ALTER TABLE ONLY public.ast_eksmo
    ADD CONSTRAINT ast_eksmo_pkey PRIMARY KEY (id);


--
-- Name: azbuka_etc azbuka_etc_pkey; Type: CONSTRAINT; Schema: public; Owner: mkniga
--

ALTER TABLE ONLY public.azbuka_etc
    ADD CONSTRAINT azbuka_etc_pkey PRIMARY KEY (id);


--
-- Name: book_tsvectors book_tsvectors_book_id_key; Type: CONSTRAINT; Schema: public; Owner: mkniga
--

ALTER TABLE ONLY public.book_tsvectors
    ADD CONSTRAINT book_tsvectors_book_id_key UNIQUE (book_id);


--
-- Name: book_tsvectors book_tsvectors_pkey; Type: CONSTRAINT; Schema: public; Owner: mkniga
--

ALTER TABLE ONLY public.book_tsvectors
    ADD CONSTRAINT book_tsvectors_pkey PRIMARY KEY (id);


--
-- Name: books books_pkey; Type: CONSTRAINT; Schema: public; Owner: mkniga
--

ALTER TABLE ONLY public.books
    ADD CONSTRAINT books_pkey PRIMARY KEY (id);


--
-- Name: individuum individuum_pkey; Type: CONSTRAINT; Schema: public; Owner: mkniga
--

ALTER TABLE ONLY public.individuum
    ADD CONSTRAINT individuum_pkey PRIMARY KEY (id);


--
-- Name: limbakh limbakh_pkey; Type: CONSTRAINT; Schema: public; Owner: mkniga
--

ALTER TABLE ONLY public.limbakh
    ADD CONSTRAINT limbakh_pkey PRIMARY KEY (id);


--
-- Name: mif mif_pkey; Type: CONSTRAINT; Schema: public; Owner: mkniga
--

ALTER TABLE ONLY public.mif
    ADD CONSTRAINT mif_pkey PRIMARY KEY (id);


--
-- Name: omega omega_pkey; Type: CONSTRAINT; Schema: public; Owner: mkniga
--

ALTER TABLE ONLY public.omega
    ADD CONSTRAINT omega_pkey PRIMARY KEY (id);


--
-- Name: polyandria polyandria_pkey; Type: CONSTRAINT; Schema: public; Owner: mkniga
--

ALTER TABLE ONLY public.polyandria
    ADD CONSTRAINT polyandria_pkey PRIMARY KEY (id);


--
-- Name: slowbooks slowbooks_pkey; Type: CONSTRAINT; Schema: public; Owner: mkniga
--

ALTER TABLE ONLY public.slowbooks
    ADD CONSTRAINT slowbooks_pkey PRIMARY KEY (id);


--
-- Name: supplier_36_6 supplier_36_6_pkey; Type: CONSTRAINT; Schema: public; Owner: mkniga
--

ALTER TABLE ONLY public.supplier_36_6
    ADD CONSTRAINT supplier_36_6_pkey PRIMARY KEY (id);


--
-- Name: updates updates_pkey; Type: CONSTRAINT; Schema: public; Owner: mkniga
--

ALTER TABLE ONLY public.updates
    ADD CONSTRAINT updates_pkey PRIMARY KEY (id);


--
-- Name: ts_all_idx; Type: INDEX; Schema: public; Owner: mkniga
--

CREATE INDEX ts_all_idx ON public.book_tsvectors USING gin (tsv_all);


--
-- Name: ts_idx; Type: INDEX; Schema: public; Owner: mkniga
--

CREATE INDEX ts_idx ON public.books USING gin (ts);


--
-- Name: tsv_author_idx; Type: INDEX; Schema: public; Owner: mkniga
--

CREATE INDEX tsv_author_idx ON public.book_tsvectors USING gin (tsv_author);


--
-- Name: tsv_isbn_idx; Type: INDEX; Schema: public; Owner: mkniga
--

CREATE INDEX tsv_isbn_idx ON public.book_tsvectors USING gin (tsv_isbn);


--
-- Name: tsv_publication_year_idx; Type: INDEX; Schema: public; Owner: mkniga
--

CREATE INDEX tsv_publication_year_idx ON public.book_tsvectors USING gin (tsv_publication_year);


--
-- Name: tsv_publisher_idx; Type: INDEX; Schema: public; Owner: mkniga
--

CREATE INDEX tsv_publisher_idx ON public.book_tsvectors USING gin (tsv_publisher);


--
-- Name: tsv_title_idx; Type: INDEX; Schema: public; Owner: mkniga
--

CREATE INDEX tsv_title_idx ON public.book_tsvectors USING gin (tsv_title);


--
-- Name: books update_tsvectors_trigger; Type: TRIGGER; Schema: public; Owner: mkniga
--

CREATE TRIGGER update_tsvectors_trigger AFTER INSERT OR UPDATE ON public.books FOR EACH ROW EXECUTE FUNCTION public.update_tsvectors();


--
-- Name: book_tsvectors book_tsvectors_book_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: mkniga
--

ALTER TABLE ONLY public.book_tsvectors
    ADD CONSTRAINT book_tsvectors_book_id_fkey FOREIGN KEY (book_id) REFERENCES public.books(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

