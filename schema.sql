DROP DATABASE photoshare;
CREATE DATABASE photoshare;
USE photoshare;

CREATE TABLE Users (
    user_id int4  AUTO_INCREMENT,
    email varchar(255) UNIQUE,
    password varchar(255),
    first_name varchar(255),
    last_name varchar(255),
    dob DATE, 
    gender varchar(255),
    hometown varchar(255),
    CONSTRAINT users_pk PRIMARY KEY (user_id)
);


CREATE TABLE Pictures (
    picture_id int4 AUTO_INCREMENT,
    imgdata longblob,
    caption VARCHAR(255),
    CONSTRAINT pictures_pk PRIMARY KEY (picture_id)
);


CREATE TABLE Albums (
    album_id int4 AUTO_INCREMENT,
    name VARCHAR(255),
    CONSTRAINT albums_pk PRIMARY KEY (album_id)
);


CREATE TABLE Comments (
    comment_id int4 AUTO_INCREMENT,
    comment_text VARCHAR(255),
    CONSTRAINT comments_pk PRIMARY KEY (comment_id)
);


CREATE TABLE Tags (
    tag_id int4 AUTO_INCREMENT,
    key_word VARCHAR(255),
    CONSTRAINT tags_pk PRIMARY KEY (tag_id)
);


CREATE TABLE Makes (
    date_made DATE,
    user_id int4,
    comment_id int4,
    CONSTRAINT makes_pk PRIMARY KEY (user_id, comment_id),
    CONSTRAINT FOREIGN KEY(user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
    CONSTRAINT FOREIGN KEY(comment_id) REFERENCES Comments(comment_id)
);


CREATE TABLE Creates (
    date_created DATE, 
    album_id int4,
    user_id int4,
    CONSTRAINT creates_pk PRIMARY KEY (user_id, album_id),
    CONSTRAINT FOREIGN KEY (album_id) REFERENCES Albums(album_id) ON DELETE CASCADE,
    CONSTRAINT FOREIGN KEY(user_id) REFERENCES Users(user_id) ON DELETE CASCADE
);


CREATE TABLE Contains (
    date_added DATE,
    album_id int4,
    picture_id int4,
    CONSTRAINT contains_pk PRIMARY KEY (album_id, picture_id),
    CONSTRAINT FOREIGN KEY(picture_id) REFERENCES Pictures (picture_id) ON DELETE CASCADE,
    CONSTRAINT FOREIGN KEY (album_id) REFERENCES Albums (album_id) ON DELETE CASCADE
);


CREATE TABLE Forms (
    date_formed DATE,
    user_id int4,
    tag_id int4,
    CONSTRAINT forms_pk PRIMARY KEY(user_id, tag_id),
    CONSTRAINT FOREIGN KEY (user_id) REFERENCES Users (user_id) ON DELETE NO ACTION,
    CONSTRAINT FOREIGN KEY (tag_id) REFERENCES Tags (tag_id) ON DELETE CASCADE
);


CREATE TABLE Friends_with (
    since DATE,
    user_id1 int4,
    user_id2 int4,
    CONSTRAINT friends_pk PRIMARY KEY (user_id1, user_id2),
    CONSTRAINT FOREIGN KEY (user_id1) REFERENCES Users(user_id),
    CONSTRAINT FOREIGN KEY (user_id2) REFERENCES Users(user_id)
);
 

CREATE TABLE Likes (
    date_liked DATE,
    user_id int4,
    picture_id int4,
    PRIMARY KEY (user_id, picture_id),
    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (picture_id) REFERENCES Pictures(picture_id) ON DELETE CASCADE
);


CREATE TABLE Has (
    tag_id int4,
    picture_id int4,
    CONSTRAINT has_pk PRIMARY KEY (tag_id, picture_id),
    CONSTRAINT FOREIGN KEY (tag_id) REFERENCES Tags (tag_id),
    CONSTRAINT FOREIGN KEY (picture_id) REFERENCES Pictures (picture_id) ON DELETE CASCADE
);


CREATE TABLE Comment_on (
    comment_date DATE,
    comment_id int4,
    picture_id int4,
    PRIMARY KEY (comment_id, picture_id),
    FOREIGN KEY (comment_id) REFERENCES Comments(comment_id),
    FOREIGN KEY (picture_id) REFERENCES Pictures(picture_id) ON DELETE CASCADE
); 

INSERT INTO Users (email, password) VALUES ('test1@bu.edu', 'test');
