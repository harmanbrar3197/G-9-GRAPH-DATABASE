// 2-hop friends-of-friends from User 1, excluding self and direct friends
MATCH (s:User {id: 1})-[:FRIENDS]-(f:User)-[:FRIENDS]-(fof:User)
WHERE fof <> s
  AND NOT EXISTS { MATCH (s)-[:FRIENDS]-(fof) }
RETURN DISTINCT fof.id AS friendOfFriend
ORDER BY friendOfFriend;

// 3-hop query: nodes reachable in exactly 3 steps; exclude start and direct friends
MATCH (s:User {id: 1})-[:FRIENDS*3]-(target:User)
WHERE target <> s
  AND NOT EXISTS { MATCH (s)-[:FRIENDS]-(target) }
RETURN DISTINCT target.id AS threeHopUser
ORDER BY threeHopUser;

// Inspect query plan (run separately)
EXPLAIN MATCH (s:User {id: 1})-[:FRIENDS]-(f)-[:FRIENDS]-(fof)
RETURN DISTINCT fof.id;
