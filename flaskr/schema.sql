-- Initialize the database.
-- Drop any existing data and create empty tables.

DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS post;
DROP TABLE IF EXISTS comment;

CREATE TABLE user (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL
);

CREATE TABLE post (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  author_id INTEGER NOT NULL,
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  title TEXT NOT NULL,
  body TEXT NOT NULL,
  image varchar(100) not null,
  like INTEGER NULL DEFAULT (0),
  FOREIGN KEY (like) REFERENCES user (id) on delete cascade
  FOREIGN KEY (author_id) REFERENCES user (id)
);

CREATE TABLE comment (
id integer PRIMARY KEY AUTOINCREMENT,
created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
author_id integer NOT NULL,
active boolean NOT NULL DEFAULT TRUE,
body text NOT NULL,
FOREIGN KEY (author_id) references post(id) on delete cascade
FOREIGN KEY (author_id) references user(id)
);
