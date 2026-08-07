from user import app

client = app.test_client()


def test_register():

    response = client.post(
        "/auth/register",
        json={
            "name": "Test User",
            "email": "testuser@example.com",
            "password": "Password123"
        }
    )

    print("Status:", response.status_code)
    print("Location:", response.headers.get("Location"))

    assert response.status_code in [201, 400]

    # If the user already exists, 400 is also acceptable
    assert response.status_code in [201, 400]


def test_login():

    response = client.post(
        "/auth/login",
        json={
            "email": "testuser@example.com",
            "password": "Password123"
        }
    )

    assert response.status_code == 200

    data = response.get_json()

    assert "token" in data


def test_get_user():

    login = client.post(
        "/auth/login",
        json={
            "email": "testuser@example.com",
            "password": "Password123"
        }
    )

    token = login.get_json()["token"]

    response = client.get(
        "/users/1",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 200


def test_create_post():

    login = client.post(
        "/auth/login",
        json={
            "email": "testuser@example.com",
            "password": "Password123"
        }
    )

    token = login.get_json()["token"]

    response = client.post(
        "/posts",
        json={
            "title": "Testing",
            "content": "My first post"
        },
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 201


def test_user_posts():

    response = client.get("/users/1/posts")

    assert response.status_code == 200


def test_users_with_posts():

    response = client.get("/users-with-posts")

    assert response.status_code == 200


def test_join_users_posts():

    response = client.get("/join/users-posts")

    assert response.status_code == 200