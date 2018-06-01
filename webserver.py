from flask import Flask, render_template, request, abort, redirect, url_for
from flask import session as fl_session
import db
from sqlalchemy import func, alias
import bcrypt
import configparser
import requests

app = Flask(__name__)

app.jinja_env.trim_blocks = True
app.jinja_env.lstrip_blocks = True

config = configparser.ConfigParser()
config.read("config.ini")

app.secret_key = config["Flask"]["secret_key"]


@app.route("/")
def page_main():
    if fl_session.get("username"):
        return render_template("main.html", easter_egg=config["Flask"]["easter_egg"])
    return redirect(url_for("page_login"))


@app.route("/login")
def page_login():
    return render_template("login.html")


@app.route("/loggedin", methods=["POST"])
def page_loggedin():
    username = request.form.get("username", "")
    password = request.form.get("password", "")
    db_session = db.Session()
    user = db_session.query(db.Royal).filter_by(username=username).one_or_none()
    db_session.close()
    if user is None:
        abort(403)
        return
    if user.password is None:
        fl_session["username"] = username
        return redirect(url_for("page_password"))
    if bcrypt.checkpw(bytes(password, encoding="utf8"), user.password):
        fl_session["username"] = username
        return redirect(url_for("page_main"))
    else:
        abort(403)
        return


@app.route("/password", methods=["GET", "POST"])
def page_password():
    username = fl_session.get("username")
    if request.method == "GET":
        if username is None:
            abort(403)
            return
        return render_template("password.html")
    elif request.method == "POST":
        new_password = request.form.get("new", "")
        db_session = db.Session()
        user = db_session.query(db.Royal).filter_by(username=username).one()
        if user.password is None:
            user.password = bcrypt.hashpw(bytes(new_password, encoding="utf8"), bcrypt.gensalt())
            db_session.commit()
            db_session.close()
            return redirect(url_for("page_main"))
        else:
            db_session.close()
            abort(403)
            return


@app.route(config["Flask"]["easter_egg"])
def page_easter_egg():
    username = fl_session.get("username")
    if username is None:
        abort(403)
        return
    db_session = db.Session()
    user = db_session.query(db.Telegram).join(db.Royal).filter_by(username=username).one()
    db_session.close()
    requests.get("https://api.telegram.org/bot490383363:AAG-_iipLeU2Vl0CfAG-YbRzy-mAndfANBc/sendDocument", params={
        "chat_id": user.telegram_id,
        "document": "BQADAgADqgEAAu2JiEjObmr6xD7y7AI",
        "caption": "Super-secret file"
    })


if __name__ == "__main__":
    try:
        app.run(host="0.0.0.0", port=1234, debug=__debug__)
    except KeyboardInterrupt:
        pass
