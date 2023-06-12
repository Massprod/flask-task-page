import pytest
import json
from database.models import Users


@pytest.mark.usefixtures
def test_register_page_credentials(test_client, t_db, user_1):
    """Testing register_page with correct/duplicated credentials"""
    with test_client as client:
        get_page: json = client.get("/register")
        assert get_page.status_code == 200
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
        duplicate: json = client.post("/register",
                                      data={
                                          "username": test_name,
                                          "password": test_pass,
                                      },
                                      )
        assert duplicate.status_code == 403
