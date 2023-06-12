from flask import Flask, render_template, request, url_for, redirect
from flask_login import LoginManager, login_user, current_user, login_required, logout_user
from database.models import Users
from database.database import Base, engine, get_session
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
    db = next(get_session())
    return db.query(Users).filter_by(id=id).first()


@app.route("/", methods=["GET"])
def redirect_main():
    return redirect(url_for("login_page"))


@app.route("/login", methods=["GET", "POST"])
def login_page():
    if current_user.is_authenticated:
        return redirect(url_for("task_page"))
    elif request.method == "POST":
        db = next(get_session())
        data = request.form
        login = requests.post(f"{api_base}token",
                              headers={"content-type": "application/x-www-form-urlencoded"},
                              data={"username": data["username"],
                                    "password": data["password"],
                                    }
                              )
        if login.status_code == 200:
            back_data: json = login.json()
            token: str = back_data["access_token"]
            user_id: int = int(back_data["user_id"])
            user_login: str = back_data["login"]
            update = db.query(Users).filter_by(id=user_id).first()
            if update is None:
                back_user = Users(id=user_id,
                                  login=user_login,
                                  token=token,
                                  )
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
            login_user(update, remember=True, duration=timedelta(minutes=1))
            return redirect(url_for("task_page"))
        elif login.status_code == 404:
            return render_template("login/login.html", name_inc=True)
        elif login.status_code == 403:
            return render_template("login/login.html", pass_inc=True)
    return render_template("login/login.html", copyright=copy_year)


@app.route("/register", methods=["GET", "POST"])
def register_page():
    if current_user.is_authenticated:
        return redirect(url_for("task_page"))
    elif request.method == "POST":
        db = next(get_session())
        data = request.form
        register = requests.post(f"{api_base}user/new",
                                 json={"login": data["username"],
                                       "password": data["password"],
                                       }
                                 )
        if register.status_code == 200:
            registered = register.json()
            new_user = Users(id=registered["id"],
                             login=registered["login"],
                             )
            db.add(new_user)
            db.commit()
            return redirect(url_for("login_page"))
        elif register.status_code == 403:
            return render_template("login/register.html", taken=data["username"], copyright=copy_year)
    return render_template("login/register.html", copyright=copy_year)


@app.route("/task", methods=["GET"])
@login_required
def task_page():
    token = current_user.token
    tasks = requests.get(f"{api_base}task/all",
                         headers={"Authorization": f"Bearer {token}"},
                         )
    if tasks.status_code == 401:
        logout_user()
        return redirect(url_for("login_page"))
    return render_template("task/task_page.html", tasks=tasks.json()["user_tasks"], copyright=copy_year)


@app.route("/task/delete", methods=["GET", "POST"])
@login_required
def delete_task():
    token = current_user.token
    if request.method == "GET":
        task_id = request.args["task_id"]
        response = requests.delete(f"{api_base}task/{task_id}",
                                   headers={"Authorization": f"Bearer {token}"},
                                   )
        if response.status_code == 401:
            logout_user()
            return redirect(url_for("login_page"))
        return redirect(url_for('task_page'))
    task_id = request.form["id"]
    new_name = request.form["taskname"]
    new_desc = request.form["taskdesc"]
    new_status = request.form["status"]
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
def add_new_task():
    token = current_user.token
    task_name = request.form["taskname"]
    task_desc = request.form["taskdesc"]
    task_status = False
    response = requests.post(f"{api_base}task/new",
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
    logout_user()
    return redirect(url_for("login_page"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=True)
