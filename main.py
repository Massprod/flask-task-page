from flask import Flask, render_template, request
from flask_login import LoginManager, UserMixin, login_user
from flask_sqlalchemy import SQLAlchemy
import requests

app = Flask(__name__)
app.secret_key = "VerySecretKek!2VerySecretKek"

api_base = "http://localhost:5000/"
login_manager = LoginManager(app=app)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


class Users(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(), nullable=False)


with app.app_context():
    db.create_all()


@login_manager.user_loader
def user_loader(id):
    return Users.query.get(int(id))


@app.route("/login", methods=["GET", "POST"])
def login_page():
    if request.method == "POST":
        print(request.form)
        data = request.form
        login = requests.post(f"{api_base}token",
                              headers={"content-type": "application/x-www-form-urlencoded"},
                              data={"username": data["username"],
                                    "password": data["password"],
                                    }
                              )
        print(login.json())
        if login.status_code == 200:
            token = login.json()["access_token"]
            return render_template("task/test.html", token=token)
        elif login.status_code == 404:
            return render_template("login/login.html", name_inc=True)
        elif login.status_code == 403:
            return render_template("login/login.html", pass_inc=True)
    return render_template("login/login.html")


@app.route("/register", methods=["GET", "POST"])
def register_page():
    if request.method == "POST":
        return render_template("task/test,html")
    return render_template("login/register.html")





if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=True)