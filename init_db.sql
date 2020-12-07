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
    PRIMARY KEY(id)
);

CREATE TABLE list_notes (
    user_id INT NOT NULL, 
    note_id INT NOT NULL AUTO_INCREMENT,
    FOREIGN KEY (user_id) REFERENCES user_list(id),
    FOREIGN KEY (note_id) REFERENCES user_notes(id),
    PRIMARY KEY (user_id, note_id)
);

CREATE TABLE admins (
    id INT AUTO_INCREMENT NOT NULL,
    public_id INT NOT NULL,
    name VARCHAR(50) NOT NULL,
    password VARCHAR(50) NOT NULL,
    admin BOOLEAN,
    PRIMARY KEY(id)
);