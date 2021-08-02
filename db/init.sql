CREATE TABLE IF NOT EXISTS top
(
    id SERIAL,
    artist text NOT NULL,
    tracks json NOT NULL,
    date date NOT NULL,
    requests integer NOT NULL,
    CONSTRAINT top_pkey PRIMARY KEY (id),
    CONSTRAINT unique_artist UNIQUE (artist)
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;
