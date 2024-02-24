CREATE TABLE IF NOT EXISTS urls (
    id bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    name varchar(255),
    created_at date
);


CREATE TABLE IF NOT EXISTS url_cheks (
    id bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    url_id varchar(255),
    status_code varchar(255),
    h1 varchar(255),
    title varchar(255),
    description varchar(255),
    created_at date
);