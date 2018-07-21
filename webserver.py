from flask import Flask, render_template, request, abort, redirect, url_for, Markup, escape
from flask import session as fl_session
import db
import bcrypt
import configparser
import markdown2
import datetime
import telegram

app = Flask(__name__)

app.jinja_env.trim_blocks = True
app.jinja_env.lstrip_blocks = True

config = configparser.ConfigParser()
config.read("config.ini")

app.secret_key = config["Flask"]["secret_key"]

telegram_bot = telegram.Bot(config["Telegram"]["bot_token"])

@app.route("/")
def page_main():
    if fl_session.get("user_id"):
        db_session = db.Session()
        royals = db_session.query(db.Royal).all()
        wiki_pages = db_session.query(db.WikiEntry).all()
        db_session.close()
        return render_template("main.html", royals=royals, wiki_pages=wiki_pages)
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
    return render_template("profile.html", ryg=user, css=css, osu=osu, rl=rl, dota=dota, lol=lol, steam=steam, ow=ow)


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
        abort(401)
        return
    if user.password is None:
        fl_session["user_id"] = user.id
        fl_session["username"] = username
        return redirect(url_for("page_password"))
    if bcrypt.checkpw(bytes(password, encoding="utf8"), user.password):
        fl_session["user_id"] = user.id
        fl_session["username"] = username
        return redirect(url_for("page_main"))
    else:
        abort(401)
        return


@app.route("/logout")
def page_logout():
    if "user_id" in fl_session:
        del fl_session["user_id"]
        del fl_session["username"]
    return redirect(url_for("page_main"))


@app.route("/password", methods=["GET", "POST"])
def page_password():
    user_id = fl_session.get("user_id")
    if request.method == "GET":
        if user_id is None:
            abort(401)
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
            abort(401)
            return


@app.route("/setcss", methods=["GET", "POST"])
def page_setcss():
    user_id = fl_session.get("user_id")
    db_session = db.Session()
    ccss = db_session.query(db.CustomCSS).filter_by(royal_id=user_id).one_or_none()
    if request.method == "GET":
        db_session.close()
        if user_id is None:
            abort(401)
            return
        return render_template("setcss.html", css=ccss.css)
    elif request.method == "POST":
        if user_id is None:
            abort(401)
            return
        css = request.form.get("css", "")
        if "</style" in css:
            abort(400)
            return
        if ccss is None:
            ccss = db.CustomCSS(royal_id=user_id, css=css)
            db_session.add(ccss)
        else:
            ccss.css = request.form.get("css", "")
        db_session.commit()
        royal = db_session.query(db.Royal).filter_by(id=user_id).one()
        db_session.close()
        return redirect(url_for("page_profile", name=royal.username))


@app.route("/game/<name>")
def page_game(name: str):
    db_session = db.Session()
    if name == "rl":
        game_name = "Rocket League"
        query = db_session.query(db.RocketLeague).join(db.Steam).all()
    elif name == "dota":
        game_name = "Dota 2"
        query = db_session.query(db.Dota).join(db.Steam).all()
    elif name == "lol":
        game_name = "League of Legends"
        query = db_session.query(db.LeagueOfLegends).all()
    elif name == "osu":
        game_name = "osu!"
        query = db_session.query(db.Osu).all()
    elif name == "ow":
        game_name = "Overwatch"
        query = db_session.query(db.Overwatch).all()
    elif name == "steam":
        game_name = "Steam"
        query = db_session.query(db.Steam).all()
    elif name == "ryg":
        game_name = "Royalnet"
        query = db_session.query(db.Royal).all()
    db_session.close()
    return render_template("game.html", minis=query, game_name=game_name, game_short_name=name)


@app.route("/wiki/<key>", methods=["GET", "POST"])
def page_wiki(key: str):
    db_session = db.Session()
    wiki_page = db_session.query(db.WikiEntry).filter_by(key=key).one_or_none()
    if request.method == "GET":
        wiki_latest_edit = db_session.query(db.WikiLog).filter_by(edited_key=key) \
                               .order_by(db.WikiLog.timestamp.desc()).first()
        db_session.close()
        if wiki_page is None:
            return render_template("wiki.html", key=key)
        converted_md = Markup(markdown2.markdown(escape(wiki_page.content),
                              extras=["spoiler", "tables"]))
        return render_template("wiki.html", key=key, wiki_page=wiki_page, converted_md=converted_md,
                               wiki_log=wiki_latest_edit)
    elif request.method == "POST":
        user_id = fl_session.get('user_id')
        user = db_session.query(db.Royal).filter_by(id=user_id).one()
        if user_id is None:
            db_session.close()
            abort(401)
            return
        if wiki_page is None:
            wiki_page = db.WikiEntry(key=key, content=request.form.get("content"))
            db_session.add(wiki_page)
            db_session.flush()
        else:
            wiki_page.content = request.form.get("content")
        edit_reason = request.form.get("reason")
        new_log = db.WikiLog(editor=user, edited_key=key, timestamp=datetime.datetime.now(), reason=edit_reason)
        db_session.add(new_log)
        db_session.commit()
        try:
            telegram_bot.send_message(config["Telegram"]["main_group"],
                                      f'ℹ️ La pagina wiki <a href="https://ryg.steffo.eu/wiki/{key}">{key}</a> è stata'
                                      f' modificata da'
                                      f' <a href="https://ryg.steffo.eu/profile/{user.username}">{user.username}</a>:'
                                      f' {"<i>Nessun motivo specificato.</i>" if not edit_reason else edit_reason}\n',
                                      parse_mode="HTML")
        except:
            pass
        return redirect(url_for("page_wiki", key=key))


if __name__ == "__main__":
    try:
        app.run(host="0.0.0.0", port=1235, debug=__debug__)
    except KeyboardInterrupt:
        pass
