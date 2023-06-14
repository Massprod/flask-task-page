import pytest
import json
from database.models import Users


@pytest.mark.usefixtures
def test_add_new_task(test_client, t_db, t_authorize, t_tasks):
    """Testing add_new_task page with authenticated User, and not authenticated."""
    with test_client as client:
        test_name: str = t_authorize["username"]
        # adding new tasks for active_user
        for task_name, task_desc in t_tasks.items():
            test_task_name: str = task_name
            test_task_desc: str = task_desc
            new_task_response: json = client.post("/task/add",
                                                  data={
                                                      "taskname": test_task_name,
                                                      "taskdesc": test_task_desc,
                                                  },
                                                  follow_redirects=True,
                                                  )
            assert new_task_response.status_code == 200
            assert len(new_task_response.history) == 1
            assert new_task_response.request.path == "/task"
        # delete/change active user token in local DB
        exist: Users | None = t_db.query(Users).filter_by(login=test_name).first()
        test_user_id: int = exist.id
        assert exist
        changed_token: str = exist.token[:len(exist.token)//2]
        t_db.query(Users).update(
            {
                Users.token: changed_token
            }
        )
        t_db.commit()
        exist = t_db.query(Users).filter_by(login=test_name).first()
        assert exist
        assert exist.token == changed_token
        assert exist.id == test_user_id
        # trying to access/add task_page without valid token on active_user
        for task_name, task_desc in t_tasks.items():
            incorrect_token_taskname: str = task_name
            incorrect_token_taskdesc: str = task_desc
            incorrect_token_response: json = client.post("/task/add",
                                                         data={
                                                             "taskname": incorrect_token_taskname,
                                                             "taskdesc": incorrect_token_taskdesc
                                                         },
                                                         follow_redirects=True,
                                                         )
            assert incorrect_token_response.status_code == 200
            assert len(incorrect_token_response.history) == 1
            assert incorrect_token_response.request.path == "/login"
            break
