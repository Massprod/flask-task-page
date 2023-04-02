from flask import Flask, render_template, request, url_for, redirect
from flask_login import LoginManager, login_user, current_user, \
    login_required, logout_user, login_fresh, login_remembered, user_logged_out
from database.models import Users
from database.database import Base, engine, get_session
import requests
from datetime import timedelta

app = Flask(__name__)
app.secret_key = "VerySecretKek!2VerySecretKek"

api_base = "http://localhost:5000/"
login_manager = LoginManager(app=app)
login_manager.login_view = "login_page"
login_manager.refresh_view = "login_page"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database/database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["TESTING"] = False

Base.metadata.create_all(engine)


@login_manager.user_loader
def user_loader(id):
    db = next(get_session())
    return db.query(Users).filter_by(id=id).first()


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
            token = login.json()["access_token"]
            user_id = int(login.json()["user_id"])
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
    print(current_user)
    return render_template("login/login.html")


@app.route("/register", methods=["GET", "POST"])
def register_page():
    if current_user.is_authenticated:
        return redirect(url_for("task_page"))
    elif request.method == "POST":
        db = next(get_session())
        data = request.form
        print(data)
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
            return render_template("login/register.html", taken=data["username"])
    return render_template("login/register.html")


@app.route("/task", methods=["GET"])
@login_required
def task_page():
    token = current_user.token
    print(token)
    tasks = requests.get(f"{api_base}task/all",
                         headers={"Authorization": f"Bearer {token}"},
                         )
    return render_template("task/test.html", tasks=tasks.json()["user_tasks"])


@app.route("/task/delete", methods=["POST"])
@login_required
def delete_task():
    task_id = request.form["id"]
    print(request.form['taskname'])
    token = current_user.token
    requests.delete(f"{api_base}task/{task_id}",
                    headers={"Authorization": f"Bearer {token}"},
                    )
    return redirect(url_for('task_page'))


@app.route("/logout")
@login_required
def logout_page():
    logout_user()
    return redirect(url_for("login_page"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=True)
