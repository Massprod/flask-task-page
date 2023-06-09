import pytest
import json
from database.models import Users
import requests


@pytest.mark.usefixtures
def test_register_page_credentials(test_client, t_db, user_1) -> None:
    """Testing register_page with correct/duplicated credentials"""
    with test_client as client:
        get_page: json = client.get("/register")
        assert get_page.status_code == 200
        # username not taken
        test_name: str = user_1["username"]
        test_pass: str = user_1["password"]
        response: json = client.post("/register",
                                     data={
                                         "username": test_name,
                                         "password": test_pass,
                                     },
                                     follow_redirects=True,
                                     )
        assert response.status_code == 200
        assert len(response.history) == 1
        assert response.request.path == "/login"
        exist: Users | None = t_db.query(Users).filter_by(login=test_name).first()
        assert exist
        assert exist.login == test_name
        # username already taken
        duplicate: json = client.post("/register",
                                      data={
                                          "username": test_name,
                                          "password": test_pass,
                                      },
                                      )
        assert duplicate.status_code == 403


@pytest.mark.usefixtures
def test_register_page_with_back_offline(test_client, user_1, mocker) -> None:
    """Testing /register POST request with back_part Offline"""
    with test_client as client:
        test_name: str = user_1["username"]
        test_pass: str = user_1["password"]
        mocker.patch("main.requests.post", side_effect=requests.exceptions.ConnectionError)
        register_response: json = client.post("/register",
                                              data={
                                                  "username": test_name,
                                                  "password": test_pass,
                                              },
                                              )
        assert register_response.status_code == 503
