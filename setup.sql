-- Starter SQL schema and 10-user sample dataset
DROP TABLE IF EXISTS friendships;
DROP TABLE IF EXISTS users;
CREATE TABLE users (id INT PRIMARY KEY, name TEXT NOT NULL);
CREATE TABLE friendships (user_a INT NOT NULL, user_b INT NOT NULL,
    CHECK (user_a <> user_b));
INSERT INTO users(id,name) VALUES
(1,'User_1'),
(2,'User_2'),
(3,'User_3'),
(4,'User_4'),
(5,'User_5'),
(6,'User_6'),
(7,'User_7'),
(8,'User_8'),
(9,'User_9'),
(10,'User_10') ;
INSERT INTO friendships(user_a,user_b) VALUES
(1,2),(1,3),(2,4),(2,5),(3,6),(3,7),(4,8),(5,9),(6,10);
-- Validate loaded sample
SELECT COUNT(*) AS user_count FROM users;
SELECT COUNT(*) AS friendship_count FROM friendships;
