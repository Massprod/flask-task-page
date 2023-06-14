import pytest
import json
from database.models import Users
from sqlalchemy.orm import Session


def ruin_token(username: str, database: Session) -> None:
    """
    Changing correct authorization token, taken as oauth2_token to make back request, to an incorrect one.

    username -> name of registered User.

    database -> db session where's correct token stored.
    """
    exist: Users | None = database.query(Users).filter_by(login=username).first()
    test_user_id: int = exist.id
    assert exist
    changed_token: str = exist.token[:len(exist.token) // 2]
    database.query(Users).update(
        {
            Users.token: changed_token
        }
    )
    database.commit()
    exist = database.query(Users).filter_by(login=username).first()
    assert exist
    assert exist.token == changed_token
    assert exist.id == test_user_id


@pytest.mark.usefixtures
def test_task_page_add_new_task(test_client, t_db, t_authorize, t_tasks) -> None:
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
        ruin_token(test_name, t_db)
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


@pytest.mark.usefixtures
def test_task_page_update_existing_tasks(test_client, t_db, t_tasks, t_authorize) -> None:
    """Testing delete_task page with updating already existing tasks for active User"""
    with test_client as client:
        test_name: str = t_authorize["username"]
        # adding test tasks
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
        # This WHOLE task_page project, doesn't work without our back_part,
        # and back_part is already 100% test covered.
        # So there's actually no reasons to test -> if task desc and name will change in DB,
        # because it's 100% going to work if back_part is running.
        # That's why I will just test -> redirecting to the /task with correct token/task_data.
        #                             -> redirecting to the /login with broken token.
        # Otherwise, it's just duplicating already existing tests for a back_part and there's no reasons to do it.
        test_task_id: int = 1  # id of the tasks is primary key in back_part db
        test_task_status: bool = True
        for task_name, task_desc in t_tasks.items():
            test_changed_name: str = task_name[:len(task_name) // 2: -1]
            test_changed_desc: str = task_desc[:len(task_desc) // 2: -1]
            update_task_response: json = client.post("/task/delete",
                                                     data={
                                                         "id": test_task_id,
                                                         "taskname": test_changed_name,
                                                         "taskdesc": test_changed_desc,
                                                         "status": test_task_status,
                                                     },
                                                     follow_redirects=True,
                                                     )
            if test_task_id == 19:
                assert update_task_response.status_code == 200
                assert len(update_task_response.history) == 1
                assert update_task_response.request.path == "/login"
                break
            assert update_task_response.status_code == 200
            assert len(update_task_response.history) == 1
            assert update_task_response.request.path == "/task"
            test_task_id += 1
            if test_task_status:
                test_task_status = False
                continue
            test_task_status = True
            if test_task_id > 18:
                ruin_token(test_name, t_db)
