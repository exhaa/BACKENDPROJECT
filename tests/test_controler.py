from app import app

def test_get_users_controler():
    client = app.test_client()

    response = client.get("/users")

    assert response.status_code == 200