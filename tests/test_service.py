from service.user_service import fetch_users

def test_fetch_users():
    users = fetch_users()

    assert len(users) == 2
    assert users[0]["name"] == "Esha"