from flask import Flask, render_template, request
import requests

app = Flask(__name__)

api_base = "http://localhost:5000/"


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
        if token := login.json()["access-token"]:
            return render_template("task/test.html")
        return render_template("login/login.html", )
    return render_template("login/login.html")


@app.route("/register", methods=["GET", "POST"])
def register_page():
    if request.method == "POST":
        return render_template("task/test,html")
    return render_template("login/register.html")





if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=True)