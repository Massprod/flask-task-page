from flask import Flask, render_template, request, url_for, redirect, Response
from flask_login import LoginManager, login_user, current_user, login_required, logout_user
from database.models import Users
from database.database import Base, engine, get_session, Session
import requests
from datetime import timedelta, datetime
import json

api_base = "http://localhost:5000/"

app = Flask(__name__)
app.secret_key = "VerySecret!2VerySecret"

login_manager = LoginManager(app=app)
login_manager.login_view = "login_page"
login_manager.refresh_view = "login_page"

Base.metadata.create_all(engine)
copy_year: str = datetime.utcnow().strftime("%Y")


@login_manager.user_loader
def user_loader(id):
    """
    Loading DB object of a user with given id.

    DB object holds:

    @local_id - id of a user on local db.

    @id - id of a user on back db.

    @login - username of a user on back/local db.

    @token - lastly assigned authorization token from back.
    :returns:
    Users - database model/table
    """
    db: Session = next(get_session())
    return db.query(Users).filter_by(id=id).first()


@app.route("/", methods=["GET"])
def redirect_main():
    """Redirecting from basic DomainName to -> /login page."""
    return redirect(url_for("login_page"))


@app.route("/login", methods=["GET", "POST"])
def login_page():
    """
    Authorizing registered users, setting session with 10m expire limit.

    If user already registered in back DB, authorizing and adding this user into a local DB.

    regex for -> Username == '^[A-Za-z0-9]{2,50}$' | limited to 50chars

    regex for -> Password == '^[A-Za-z0-9@$!%*#?&]{8,100}$' | limited to 8-100chars
    """
    if current_user.is_authenticated:
        return redirect(url_for("task_page"))
    elif request.method == "POST":
        db: Session = next(get_session())
        data: json = request.form
        try:
            login: json = requests.post(f"{api_base}token",
                                        headers={"content-type": "application/x-www-form-urlencoded"},
                                        data={"username": data["username"],
                                              "password": data["password"],
                                              }
                                        )
        except requests.exceptions.ConnectionError:
            return render_template("login/login.html", back_down=True, copyright=copy_year), 503
        if login.status_code == 200:
            back_data: json = login.json()
            token: str = back_data["access_token"]
            user_id: int = int(back_data["user_id"])
            user_login: str = back_data["login"]
            update: Users = db.query(Users).filter_by(id=user_id).first()
            if update is None:
                back_user: Users = Users()
                back_user.id = user_id
                back_user.login = user_login
                back_user.token = token
                db.add(back_user)
                db.commit()
            else:
                db.query(Users).filter_by(id=user_id).update(
                    {
                        Users.token: token
                    }
                )
                db.commit()
            update = db.query(Users).filter_by(id=user_id).first()
            login_user(update, remember=True, duration=timedelta(minutes=10))
            return redirect(url_for("task_page"))
        elif login.status_code == 404:
            return render_template("login/login.html", name_inc=True), 404
        elif login.status_code == 403:
            return render_template("login/login.html", pass_inc=True), 403
    return render_template("login/login.html", copyright=copy_year)


@app.route("/register", methods=["GET", "POST"])
def register_page():
    """
    Adding new users into local/back db, if Username isn't already taken.

    regex for -> Username == '^[A-Za-z0-9]{2,50}$' | limited to 50chars

    regex for -> Password == '^[A-Za-z0-9@$!%*#?&]{8,100}$'
    """
    if current_user.is_authenticated:
        return redirect(url_for("task_page"))
    elif request.method == "POST":
        db: Session = next(get_session())
        data: json = request.form
        try:
            register: Response = requests.post(f"{api_base}user/new",
                                               json={"login": data["username"],
                                                     "password": data["password"],
                                                     }
                                               )
        except requests.exceptions.ConnectionError:
            return render_template("login/register.html", back_down=True, copyright=copy_year), 503
        if register.status_code == 200:
            registered: json = register.json()
            new_user: Users = Users()
            new_user.id = registered["id"]
            new_user.login = registered["login"]
            db.add(new_user)
            db.commit()
            return redirect(url_for("login_page"))
        elif register.status_code == 403:
            return render_template("login/register.html", taken=data["username"], copyright=copy_year), 403
    return render_template("login/register.html", copyright=copy_year)


@app.route("/task", methods=["GET"])
@login_required
def task_page():
    """
    Display every existing task for a currently active User.

    Loaded from a back DB.
    """
    token: str = current_user.token
    tasks: json = requests.get(f"{api_base}task/all",
                               headers={"Authorization": f"Bearer {token}"},
                               )
    if tasks.status_code == 401:
        logout_user()
        return redirect(url_for("login_page"))
    return render_template("task/task_page.html", tasks=tasks.json()["user_tasks"], copyright=copy_year)


@app.route("/task/delete", methods=["GET", "POST"])
@login_required
def delete_task():
    """
    Delete/Update already existed tasks for the active User.

    Redirecting to -> /task , with all updated tasks of a User on success.

    Redirecting to -> /login , if current User doesn't have authorized token.

    No limits on what symbols can be used for a taskname or taskdesc.
    """
    token: str = current_user.token
    if request.method == "GET":
        task_id: str = request.args["task_id"]
        response: json = requests.delete(f"{api_base}task/{task_id}",
                                         headers={"Authorization": f"Bearer {token}"},
                                         )
        if response.status_code == 401:
            logout_user()
            return redirect(url_for("login_page"))
        return redirect(url_for('task_page'))
    task_id: str = request.form["id"]
    new_name: str = request.form["taskname"]
    new_desc: str = request.form["taskdesc"]
    new_status: str = request.form["status"]
    response = requests.put(f"{api_base}task/{task_id}",
                            json={"name": new_name,
                                  "description": new_desc,
                                  "status": new_status,
                                  },
                            headers={"Authorization": f"Bearer {token}"},
                            )
    if response.status_code == 401:
        logout_user()
        return redirect(url_for("login_page"))
    return redirect(url_for("task_page"))


@app.route("/task/add", methods=["POST"])
@login_required
def add_new_task():
    """
    Adding new task into a back DB for the currently active User.

    Redirecting to -> /task , with all tasks of a User on success.

    Redirecting to -> /login , if current User doesn't have authorized token.

    No limits on what symbols can be used for a taskname or taskdesc.
    """
    token: str = current_user.token
    task_name: str = request.form["taskname"]
    task_desc: str = request.form["taskdesc"]
    task_status: bool = False
    response: json = requests.post(f"{api_base}task/new",
                                   json={"name": task_name,
                                         "description": task_desc,
                                         "status": task_status,
                                         },
                                   headers={"Authorization": f"Bearer {token}"}
                                   )
    if response.status_code == 401:
        logout_user()
        return redirect(url_for("login_page"))
    return redirect(url_for("task_page"))


@app.route("/logout", methods=["GET"])
@login_required
def logout_page():
    """Logout and redirect to -> /login , currently active User."""
    logout_user()
    return redirect(url_for("login_page"))
