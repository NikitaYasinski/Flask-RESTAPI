CREATE DATABASE IF NOT EXISTS users;

USE users;

CREATE TABLE user_list (
    id INT AUTO_INCREMENT NOT NULL,
    name VARCHAR(20) NOT NULL,
    city VARCHAR(20) NOT NULL,
    PRIMARY KEY(id)
);

CREATE TABLE user_notes (
    id INT AUTO_INCREMENT NOT NULL,
    title VARCHAR(20) NOT NULL,
    content VARCHAR(100) NOT NULL,
    user_id INT, 
    PRIMARY KEY(id),
    FOREIGN KEY (user_id) REFERENCES user_list (id)
);