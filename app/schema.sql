CREATE TABLE IF NOT EXISTS photo (
    id integer PRIMARY KEY AUTOINCREMENT,
    original_filename text,
    filename uuid,
    location text,
    user text,
    created_at timestamp with time zone NOT NULL DEFAULT current_timestamp
);

CREATE TABLE IF NOT EXISTS location (
    id integer PRIMARY KEY AUTOINCREMENT,
    name text NOT NULL UNIQUE,
    created_at timestamp with time zone NOT NULL DEFAULT current_timestamp
);

CREATE TABLE IF NOT EXISTS user (
    id integer PRIMARY KEY AUTOINCREMENT,
    user_id text NOT NULL UNIQUE,
    phone_number text, 
    created_at timestamp with time zone NOT NULL DEFAULT current_timestamp
);
