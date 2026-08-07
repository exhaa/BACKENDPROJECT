SELECT users.name, posts.title
FROM users
INNER JOIN posts
ON users.id = posts.user_id;