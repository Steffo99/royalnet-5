from flask import Flask, render_template, request, abort, redirect, url_for
from flask import session as fl_session
import db
from sqlalchemy import func, alias
import bcrypt
import configparser

app = Flask(__name__)

app.jinja_env.trim_blocks = True
app.jinja_env.lstrip_blocks = True

config = configparser.ConfigParser()
config.read("config.ini")

app.secret_key = config["Flask"]["secret_key"]


@app.route("/")
def page_index():
    return render_template("index.html")


@app.route("/diario")
def page_diario():
    db_session = db.Session()
    diario_data = db_session.query(db.Diario).outerjoin((db.Telegram, db.Diario.author), aliased=True).outerjoin(db.Royal, aliased=True).outerjoin((db.Telegram, db.Diario.saver), aliased=True).outerjoin(db.Royal, aliased=True).all()
    db_session.close()
    return render_template("diario.html", diario_data=diario_data)


@app.route("/leaderboards")
def page_leaderboards():
    db_session = db.Session()
    dota_data = db_session.query(db.Dota).join(db.Steam).join(db.Royal).order_by(db.Dota.rank_tier).all()
    rl_data = db_session.query(db.RocketLeague).join(db.Steam).join(db.Royal).order_by(db.RocketLeague.doubles_mmr).all()
    ow_data = db_session.query(db.Overwatch).join(db.Royal).order_by(db.Overwatch.rank).all()
    osu_data = db_session.query(db.Osu).join(db.Royal).order_by(db.Osu.std_pp).all()
    lol_data = db_session.query(db.LeagueOfLegends).join(db.Royal).order_by(db.LeagueOfLegends.summoner_name).all()
    db_session.close()
    return render_template("leaderboards.html", dota_data=dota_data, rl_data=rl_data, ow_data=ow_data, osu_data=osu_data, lol_data=lol_data)


@app.route("/music")
def page_music():
    db_session = db.Session()
    music_counts = db_session.query(db.PlayedMusic.filename, alias(func.count(db.PlayedMusic.filename), "count")).order_by("count").group_by(db.PlayedMusic.filename).all()
    music_last = db_session.query(db.PlayedMusic).join(db.Discord).join(db.Royal).order_by(db.PlayedMusic.id.desc()).limit(50).all()
    db_session.close()
    return render_template("music.html", music_counts=music_counts, music_last=music_last)


@app.route("/login")
def page_login():
    return render_template("login.html")


@app.route("/loggedin", methods=["GET", "POST"])
def page_loggedin():
    if request.method == "GET":
        username = fl_session.get("username")
        if username is None:
            return "Not logged in"
        else:
            return username
    elif request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        db_session = db.Session()
        user = db_session.query(db.Royal).filter_by(username=username).one_or_none()
        db_session.close()
        if bcrypt.checkpw(bytes(password, encoding="utf8"), user.password):
            fl_session["username"] = username
            return username
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
        old_password = request.form["old"]
        new_password = request.form["new"]
        db_session = db.Session()
        user = db_session.query(db.Royal).filter_by(username=username).one_or_none()
        if bcrypt.checkpw(bytes(old_password, encoding="utf8"), user.password):
            user.password = bcrypt.hashpw(bytes(new_password, encoding="utf8"), bcrypt.gensalt())
            db_session.commit()
            db_session.close()
            return "Password changed"
        else:
            db_session.close()
            abort(403)

if __name__ == "__main__":
    try:
        app.run(host="0.0.0.0", port=1234)
    except KeyboardInterrupt:
        pass
