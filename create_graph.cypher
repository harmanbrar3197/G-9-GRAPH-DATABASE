// Starter example: create a small graph of 10 users and 9 undirected friendships
// For the larger CSV dataset, see README.md instructions (load CSV in Aura import workflow).
CREATE (:User {id: 1, name: 'User_1'}), (:User {id: 2, name: 'User_2'}),
       (:User {id: 3, name: 'User_3'}), (:User {id: 4, name: 'User_4'}),
       (:User {id: 5, name: 'User_5'}), (:User {id: 6, name: 'User_6'}),
       (:User {id: 7, name: 'User_7'}), (:User {id: 8, name: 'User_8'}),
       (:User {id: 9, name: 'User_9'}), (:User {id: 10, name: 'User_10'});

MATCH (a:User), (b:User)
WHERE (a.id = 1 AND b.id = 2) OR (a.id = 1 AND b.id = 3)
   OR (a.id = 2 AND b.id = 4) OR (a.id = 2 AND b.id = 5)
   OR (a.id = 3 AND b.id = 6) OR (a.id = 3 AND b.id = 7)
   OR (a.id = 4 AND b.id = 8) OR (a.id = 5 AND b.id = 9)
   OR (a.id = 6 AND b.id = 10)
CREATE (a)-[:FRIENDS]-(b);

// Counts (relationship count is undirected, count each relationship once)
MATCH (u:User) RETURN count(u) AS user_count;
MATCH ()-[r:FRIENDS]-() RETURN count(r)/2 AS friendship_count;
