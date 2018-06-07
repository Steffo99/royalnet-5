from flask import Flask, render_template, request, abort, redirect, url_for
from flask import session as fl_session
import db
import bcrypt
import configparser

app = Flask(__name__)

app.jinja_env.trim_blocks = True
app.jinja_env.lstrip_blocks = True

config = configparser.ConfigParser()
config.read("config.ini")

app.secret_key = config["Flask"]["secret_key"]


@app.route("/")
def page_main():
    if fl_session.get("user_id"):
        db_session = db.Session()
        royals = db_session.query(db.Royal).all()
        db_session.close()
        return render_template("main.html", royals=royals)
    return redirect(url_for("page_login"))


@app.route("/profile/<name>")
def page_profile(name: str):
    db_session = db.Session()
    user = db_session.query(db.Royal).filter_by(username=name).one_or_none()
    if user is None:
        db_session.close()
        abort(404)
        return
    css = db_session.query(db.CustomCSS).filter_by(royal=user).one_or_none()
    steam = db_session.query(db.Steam).filter_by(royal=user).one_or_none()
    osu = db_session.query(db.Osu).filter_by(royal=user).one_or_none()
    rl = db_session.query(db.RocketLeague).join(db.Steam).filter_by(royal=user).one_or_none()
    dota = db_session.query(db.Dota).join(db.Steam).filter_by(royal=user).one_or_none()
    lol = db_session.query(db.LeagueOfLegends).filter_by(royal=user).one_or_none()
    ow = db_session.query(db.Overwatch).filter_by(royal=user).one_or_none()
    db_session.close()
    return render_template("profile.html", royal=user, css=css, osu=osu, rl=rl, dota=dota, lol=lol, steam=steam, ow=ow)


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
        fl_session["user_id"] = user.id
        return redirect(url_for("page_password"))
    if bcrypt.checkpw(bytes(password, encoding="utf8"), user.password):
        fl_session["user_id"] = user.id
        return redirect(url_for("page_main"))
    else:
        abort(403)
        return


@app.route("/password", methods=["GET", "POST"])
def page_password():
    user_id = fl_session.get("user_id")
    if request.method == "GET":
        if user_id is None:
            abort(403)
            return
        return render_template("password.html")
    elif request.method == "POST":
        new_password = request.form.get("new", "")
        db_session = db.Session()
        user = db_session.query(db.Royal).filter_by(id=user_id).one()
        if user.password is None:
            user.password = bcrypt.hashpw(bytes(new_password, encoding="utf8"), bcrypt.gensalt())
            db_session.commit()
            db_session.close()
            return redirect(url_for("page_main"))
        else:
            db_session.close()
            abort(403)
            return


@app.route("/setcss", methods=["GET", "POST"])
def page_setcss():
    user_id = fl_session.get("user_id")
    db_session = db.Session()
    ccss = db_session.query(db.CustomCSS).filter_by(royal_id=user_id).one_or_none()
    if request.method == "GET":
        db_session.close()
        if user_id is None:
            abort(403)
            return
        return render_template("setcss.html", css=ccss.css)
    elif request.method == "POST":
        if user_id is None:
            abort(403)
            return
        if ccss is None:
            ccss = db.CustomCSS(royal_id=user_id, css=request.form.get("css", ""))
            db_session.add(ccss)
        else:
            ccss.css = request.form.get("css", "")
        db_session.commit()
        royal = db_session.query(db.Royal).filter_by(id=user_id).one()
        db_session.close()
        return redirect(url_for("page_profile", name=royal.username))


if __name__ == "__main__":
    try:
        app.run(host="0.0.0.0", port=1234, debug=__debug__)
    except KeyboardInterrupt:
        pass
