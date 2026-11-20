-- 2-hop friends-of-friends from user 1, excluding self and direct friends
WITH RECURSIVE walk(id, depth, path) AS (
    SELECT 1, 0, ARRAY[1]
    UNION ALL
    SELECT CASE WHEN f.user_a = w.id THEN f.user_b ELSE f.user_a END,
           w.depth + 1,
           w.path || CASE WHEN f.user_a = w.id THEN f.user_b ELSE f.user_a END
    FROM walk w
    JOIN friendships f ON f.user_a = w.id OR f.user_b = w.id
    WHERE w.depth < 2
      AND NOT (CASE WHEN f.user_a = w.id THEN f.user_b ELSE f.user_a END = ANY(w.path))
)
SELECT DISTINCT id AS friend_of_friend
FROM walk
WHERE depth = 2 AND id <> 1
  AND id NOT IN (
      SELECT CASE WHEN user_a = 1 THEN user_b ELSE user_a END
      FROM friendships WHERE user_a = 1 OR user_b = 1
  )
ORDER BY friend_of_friend;

-- 3-hop traversal (paths cannot repeat a node)
WITH RECURSIVE walk(id, depth, path) AS (
    SELECT 1, 0, ARRAY[1]
    UNION ALL
    SELECT CASE WHEN f.user_a = w.id THEN f.user_b ELSE f.user_a END,
           w.depth + 1,
           w.path || CASE WHEN f.user_a = w.id THEN f.user_b ELSE f.user_a END
    FROM walk w
    JOIN friendships f ON f.user_a = w.id OR f.user_b = w.id
    WHERE w.depth < 3
      AND NOT (CASE WHEN f.user_a = w.id THEN f.user_b ELSE f.user_a END = ANY(w.path))
)
SELECT DISTINCT id AS three_hop_user FROM walk
WHERE depth = 3 AND id <> 1
ORDER BY three_hop_user;

-- Basic EXPLAIN plan (run separately if the playground supports it)
EXPLAIN WITH RECURSIVE walk(id, depth, path) AS (
    SELECT 1, 0, ARRAY[1]
    UNION ALL
    SELECT CASE WHEN f.user_a = w.id THEN f.user_b ELSE f.user_a END,
           w.depth + 1, w.path || CASE WHEN f.user_a = w.id THEN f.user_b ELSE f.user_a END
    FROM walk w JOIN friendships f ON f.user_a = w.id OR f.user_b = w.id
    WHERE w.depth < 2 AND NOT (CASE WHEN f.user_a = w.id THEN f.user_b ELSE f.user_a END = ANY(w.path))
) SELECT DISTINCT id FROM walk WHERE depth = 2;
