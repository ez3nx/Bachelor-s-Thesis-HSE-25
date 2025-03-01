CREATE TABLE IF NOT EXISTS tcs_pulse_posts_sber (
    id integer PRIMARY KEY AUTOINCREMENT,
    post_id text UNIQUE,
    inserted text null,
    instruments text null,
    hashtags text null,
    content text null,
    reactions_count integer null,
    comments_count integer null,
    parse_dt text not null
);