import pytest
from main import app
from string import ascii_letters, ascii_lowercase
from random import choice
from database.database import get_session
from sqlalchemy.orm import Session
from random import randint
import json


@pytest.fixture(scope="session")
def test_client() -> app:
    """Test client for the flask APP"""
    yield app.test_client()


@pytest.fixture(autouse=True)
def logout(test_client) -> None:
    """Logout after every test with active user"""
    test_client.get("/logout")


@pytest.fixture(scope="function")
def back_base() -> str:
    """Back URL"""
    return "http://localhost:5000/"


@pytest.fixture(scope="function")
def t_db() -> Session:
    """Test DB session"""
    return next(get_session())


@pytest.fixture(scope="function")
def user_1() -> dict[str, str]:
    """Test user credentials for login, register"""
    # can't found how to add DB into a flask as I used in FastAPI dependencies,
    # using same DB for now, and creating usernames like this to at least test with that.
    # Even if I use FlaskSQLAlchemy to create db, it's still will be overriding.
    test_name: str = ""
    for _ in range(25):
        test_name += choice(ascii_lowercase)
        test_name += str(randint(0, 9))
    test_user: dict[str, str] = {
        "username": test_name,
        "password": "testPass12345678901@$!%*#?&"
    }
    return test_user


@pytest.fixture(scope="function")
def t_tasks() -> dict[str, str]:
    """Test tasks to add/update"""
    test_tasks: dict[str, str] = {}
    for _ in range(0, 20):
        task_name: str = ""
        for _ in range(0, 13):
            task_name += choice(ascii_letters)
        task_desc: str = ""
        for _ in range(0, 300):
            task_desc += choice(ascii_letters)
        test_tasks[task_name] = task_desc
    return test_tasks


@pytest.fixture(scope="function")
def t_authorize(test_client, user_1) -> dict[str, str]:
    """Create and login user to test with"""
    with test_client as client:
        test_name: str = user_1["username"]
        test_pass: str = user_1["password"]
        test_register: json = client.post("/register",
                                          data={
                                              "username": test_name,
                                              "password": test_pass,
                                          },
                                          )
        assert test_register.status_code == 302
        test_login: json = client.post("/login",
                                       data={
                                           "username": test_name,
                                           "password": test_pass,
                                       },
                                       )
        assert test_login.status_code == 302
        return user_1.copy()
