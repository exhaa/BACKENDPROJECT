import os
import sys
import pytest
from user import app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))




@pytest.fixture
def client():
    app.config["TESTING"] = True

    with app.test_client() as client:
        yield client