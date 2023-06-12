import pytest
import json
from database.models import Users
import requests


@pytest.mark.usefixtures
def test_login_page_credentials(test_client, t_db, user_1):
    """Testing login_page with correct/incorrect credentials, extra test for logout"""
    with test_client as client:
        get_page: json = client.get("/login")
        assert get_page.status_code == 200
        test_name: str = user_1["username"]
        test_pass: str = user_1["password"]
        # registering new_user to use test by itself
        register: json = client.post("/register",
                                     data={
                                         "username": test_name,
                                         "password": test_pass,
                                     },
                                     follow_redirects=True,
                                     )
        assert register.status_code == 200
        assert len(register.history) == 1
        assert register.request.path == "/login"
        # login with correct_registered credentials
        correct_login: json = client.post("/login",
                                          data={
                                              "username": test_name,
                                              "password": test_pass,
                                          },
                                          follow_redirects=True,
                                          )
        assert correct_login.status_code == 200
        assert len(correct_login.history) == 1
        assert correct_login.request.path == "/task"
        # redirect if we're having session, 10m expire time
        remembered: json = client.get("/login",
                                      follow_redirects=True,
                                      )
        assert remembered.status_code == 200
        assert len(remembered.history) == 1
        assert remembered.request.path == "/task"
        # reset
        reset: json = client.get("/logout",
                                 follow_redirects=True,
                                 )
        assert reset.status_code == 200
        assert len(reset.history) == 1
        assert reset.request.path == "/login"
        # incorrect credentials
        incorrect_login: json = client.post("/login",
                                            data={
                                                "username": test_name[:-5],
                                                "password": test_pass,
                                            },
                                            )
        assert incorrect_login.status_code == 404
        exist: Users | None = t_db.query(Users).filter_by(login=test_name[:-5]).first()
        assert exist is None
        incorrect_pass: json = client.post("/login",
                                           data={
                                               "username": test_name,
                                               "password": test_pass[:-10],
                                           },
                                           )
        assert incorrect_pass.status_code == 403
        exist = t_db.query(Users).filter_by(login=test_name).first()
        assert exist
        assert exist.login == test_name


@pytest.mark.usefixtures
def test_login_for_not_clear_back_db(test_client, t_db, user_1):
    """Testing the case when our back DB having some pre_recorded users, and we're starting a new local DB"""
    with test_client as client:
        back_base: str = "http://localhost:5000/"
        test_name: str = user_1["username"]
        test_pass: str = user_1["password"]
        back_record: json = requests.post(f"{back_base}user/new",
                                          json={
                                              "login": test_name,
                                              "password": test_pass,
                                          }
                                          )
        assert back_record.status_code == 200
        exist: Users | None = t_db.query(Users).filter_by(login=test_name).first()
        assert not exist
        # login from back DB
        old_login: json = client.post("/login",
                                      data={
                                          "username": test_name,
                                          "password": test_pass,
                                      },
                                      follow_redirects=True,
                                      )
        assert old_login.status_code == 200
        assert len(old_login.history) == 1
        assert old_login.request.path == "/task"
        exist = t_db.query(Users).filter_by(login=test_name).first()
        assert exist
        assert exist.login == test_name
        # skipped part in register_page, because there was no login cases
        register_redirect: json = client.get("/register",
                                             follow_redirects=True,
                                             )
        assert register_redirect.status_code == 200
        assert len(register_redirect.history) == 1
        assert register_redirect.request.path == "/task"
