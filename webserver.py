import secrets
from flask import Flask, render_template, request, abort, redirect, url_for, Markup, escape, jsonify
from flask import session as fl_session
from flask import g as fl_g
import db
import bcrypt
import configparser
import markdown2
import datetime
import telegram
import query_discord_music
import random
import re
from raven.contrib.flask import Sentry

app = Flask(__name__)

app.jinja_env.trim_blocks = True
app.jinja_env.lstrip_blocks = True

config = configparser.ConfigParser()
config.read("config.ini")

app.secret_key = config["Flask"]["secret_key"]

telegram_bot = telegram.Bot(config["Telegram"]["bot_token"])

sentry = Sentry(app, dsn=config["Sentry"]["token"])


@app.errorhandler(400)
def error_400(_=None):
    return render_template("400.html", g=fl_g)


@app.route("/400")
def page_400():
    return error_400()


@app.errorhandler(403)
def error_403(_=None):
    return render_template("403.html", g=fl_g)


@app.route("/403")
def page_403():
    return error_403()


@app.errorhandler(500)
def error_500(_=None):
    return render_template("500.html", g=fl_g)


@app.route("/500")
def page_500():
    return error_500()


@app.route("/")
def page_main():
    if not fl_session.get("user_id"):
        return redirect(url_for("page_login"))
    db_session = db.Session()
    royals = db_session.query(db.Royal).order_by(db.Royal.username).all()
    wiki_pages = db_session.query(db.WikiEntry).order_by(db.WikiEntry.key).all()
    random_diario = db_session.query(db.Diario).order_by(db.func.random()).first()
    next_events = db_session.query(db.Event).filter(db.Event.time > datetime.datetime.now()).order_by(
        db.Event.time).all()
    halloween = db.Halloween.puzzle_status()[1]
    db_session.close()
    return render_template("main.html", royals=royals, wiki_pages=wiki_pages, entry=random_diario,
                           next_events=next_events, g=fl_g, escape=escape, halloween=enumerate(halloween))


@app.route("/profile/<name>")
def page_profile(name: str):
    db_session = db.Session()
    user = db_session.query(db.Royal).filter_by(username=name).one_or_none()
    if user is None:
        db_session.close()
        abort(404)
        return
    css = db_session.query(db.ProfileData).filter_by(royal=user).one_or_none()
    steam = db_session.query(db.Steam).filter_by(royal=user).one_or_none()
    osu = db_session.query(db.Osu).filter_by(royal=user).one_or_none()
    dota = db_session.query(db.Dota).join(db.Steam).filter_by(royal=user).one_or_none()
    lol = db_session.query(db.LeagueOfLegends).filter_by(royal=user).one_or_none()
    ow = db_session.query(db.Overwatch).filter_by(royal=user).one_or_none()
    tg = db_session.query(db.Telegram).filter_by(royal=user).one_or_none()
    discord = db_session.execute(query_discord_music.one_query, {"royal": user.id}).fetchone()
    gamelog = db_session.query(db.GameLog).filter_by(royal=user).one_or_none()
    halloween = db_session.query(db.Halloween).filter_by(royal=user).one_or_none()
    db_session.close()
    if css is not None:
        converted_bio = Markup(markdown2.markdown(css.bio.replace("<", "&lt;"),
                               extras=["spoiler", "tables", "smarty-pants", "fenced-code-blocks"]))
    else:
        converted_bio = ""
    return render_template("profile.html", ryg=user, css=css, osu=osu, dota=dota, lol=lol, steam=steam, ow=ow,
                           tg=tg, discord=discord, g=fl_g, bio=converted_bio, gamelog=gamelog,
                           halloween=halloween)


@app.route("/login")
def page_login():
    return render_template("login.html", g=fl_g)


@app.route("/loggedin", methods=["POST"])
def page_loggedin():
    username = request.form.get("username", "")
    password = request.form.get("password", "")
    db_session = db.Session()
    user = db_session.query(db.Royal).filter_by(username=username).one_or_none()
    db_session.close()
    fl_session.permanent = True
    if user is None:
        abort(403)
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
        abort(403)
        return


@app.route("/logout")
def page_logout():
    if "user_id" in fl_session:
        del fl_session["user_id"]
        del fl_session["username"]
    return redirect(url_for("page_main"))


@app.route("/password", methods=["GET", "POST"])
def page_password():
    if not fl_session.get("user_id"):
        return redirect(url_for("page_login"))
    user_id = fl_session.get("user_id")
    if request.method == "GET":
        if user_id is None:
            return redirect(url_for("page_login"))
        return render_template("password.html", g=fl_g)
    elif request.method == "POST":
        new_password = request.form.get("new", "")
        db_session = db.Session()
        user = db_session.query(db.Royal).filter_by(id=user_id).one()
        if user.password is None:
            user.password = bcrypt.hashpw(bytes(new_password, encoding="utf8"), bcrypt.gensalt())
            user.fiorygi += 1
            db_session.commit()
            db_session.close()
            return redirect(url_for("page_main"))
        else:
            db_session.close()
            return redirect(url_for("page_login"))


@app.route("/editprofile", methods=["GET", "POST"])
def page_editprofile():
    user_id = fl_session.get("user_id")
    if not user_id:
        return redirect(url_for("page_login"))
    db_session = db.Session()
    profile_data = db_session.query(db.ProfileData).filter_by(royal_id=user_id).join(db.Royal).one_or_none()
    if request.method == "GET":
        db_session.close()
        return render_template("profileedit.html", data=profile_data, g=fl_g)
    elif request.method == "POST":
        css = request.form.get("css", "")
        bio = request.form.get("bio", "")
        if "</style" in css:
            abort(400)
            return
        if profile_data is None:
            profile_data = db.ProfileData(royal_id=user_id, css=css, bio=bio)
            db_session.add(profile_data)
            db_session.flush()
            profile_data.royal.fiorygi += 1
            try:
                telegram_bot.send_message(config["Telegram"]["main_group"],
                                          f'⭐️ {profile_data.royal.username} ha configurato la sua bio su Royalnet e ha ottenuto un fioryg!',
                                          parse_mode="HTML", disable_web_page_preview=True, disable_notification=True)
            except Exception:
                pass
        else:
            profile_data.css = css
            profile_data.bio = bio
        db_session.commit()
        royal = db_session.query(db.Royal).filter_by(id=user_id).one()
        db_session.close()
        return redirect(url_for("page_profile", name=royal.username))


@app.route("/game/<name>")
def page_game(name: str):
    db_session = db.Session()
    if name == "rl":
        game_name = "Rocket League"
        query = db_session.query(db.RocketLeague).join(db.Steam).order_by(db.RocketLeague.solo_std_rank).all()
    elif name == "dota":
        game_name = "Dota 2"
        query = db_session.query(db.Dota).join(db.Steam).order_by(db.Dota.rank_tier.desc().nullslast()).all()
    elif name == "lol":
        game_name = "League of Legends"
        query = db_session.query(db.LeagueOfLegends).order_by(db.LeagueOfLegends.solo_division.desc().nullslast(),
                                                              db.LeagueOfLegends.solo_rank,
                                                              db.LeagueOfLegends.flex_division.desc().nullslast(),
                                                              db.LeagueOfLegends.flex_rank,
                                                              db.LeagueOfLegends.twtr_division.desc().nullslast(),
                                                              db.LeagueOfLegends.twtr_rank,
                                                              db.LeagueOfLegends.level).all()
    elif name == "osu":
        game_name = "osu!"
        query = db_session.query(db.Osu).order_by(db.Osu.mania_pp.desc().nullslast()).all()
    elif name == "ow":
        game_name = "Overwatch"
        query = db_session.query(db.Overwatch).order_by(db.Overwatch.rank.desc().nullslast()).all()
    elif name == "steam":
        game_name = "Steam"
        query = db_session.query(db.Steam).order_by(db.Steam.persona_name).all()
    elif name == "ryg":
        game_name = "Royalnet"
        query = db_session.query(db.Royal).order_by(db.Royal.username).all()
    elif name == "tg":
        game_name = "Telegram"
        query = db_session.query(db.Telegram).order_by(db.Telegram.telegram_id).all()
    elif name == "discord":
        game_name = "Discord"
        query = [dict(row) for row in db_session.execute(query_discord_music.all_query)]
    elif name == "halloween":
        game_name = "Rituale di Halloween"
        query = db_session.query(db.Halloween).all()
    else:
        abort(404)
        return
    db_session.close()
    return render_template("game.html", minis=query, game_name=game_name, game_short_name=name, g=fl_g)


@app.route("/wiki")
def page_wikihome():
    db_session = db.Session()
    wiki_pages = db_session.query(db.WikiEntry).order_by(db.WikiEntry.key).all()
    db_session.close()
    return render_template("wikilist.html", wiki_pages=wiki_pages, g=fl_g)


@app.route("/wiki/<key>", methods=["GET", "POST"])
def page_wiki(key: str):
    db_session = db.Session()
    wiki_page = db_session.query(db.WikiEntry).filter_by(key=key).one_or_none()
    if request.method == "GET":
        wiki_latest_edit = db_session.query(db.WikiLog).filter_by(edited_key=key) \
            .order_by(db.WikiLog.timestamp.desc()).first()
        db_session.close()
        if wiki_page is None:
            return render_template("wikipage.html", key=key, g=fl_g)
        # Embed YouTube videos
        converted_md = markdown2.markdown(wiki_page.content.replace("<", "&lt;"),
                                          extras=["spoiler", "tables", "smarty-pants", "fenced-code-blocks"])
        converted_md = re.sub(r"{https?:\/\/(?:www\.)?(?:youtube\.com\/watch\?.*?&?v=|youtu.be\/)([0-9A-Za-z-]+).*?}",
               r'<div class="youtube-embed">'
               r'   <iframe src="https://www.youtube-nocookie.com/embed/\1?rel=0&amp;showinfo=0" frameborder="0"'
               r' allow="autoplay; encrypted-media" allowfullscreen width="640px" height="320px"></iframe>'
               r'</div>', converted_md)
        converted_md = re.sub(r"{https?:\/\/clyp.it\/([a-z0-9]+)}",
                              r'<div class="clyp-embed">'
                              r'    <iframe width="100%" height="160" src="https://clyp.it/\1/widget" frameborder="0">'
                              r'    </iframe>'
                              r'</div>', converted_md)
        return render_template("wikipage.html", key=key, wiki_page=wiki_page, converted_md=Markup(converted_md),
                               wiki_log=wiki_latest_edit, g=fl_g)
    elif request.method == "POST":
        user_id = fl_session.get('user_id')
        user = db_session.query(db.Royal).filter_by(id=user_id).one()
        if user_id is None:
            db_session.close()
            return redirect(url_for("page_login"))
        new_content = request.form.get("content")
        # Create new page
        if wiki_page is None:
            difference = len(new_content)
            wiki_page = db.WikiEntry(key=key, content=new_content)
            db_session.add(wiki_page)
            db_session.flush()
        # Edit existing page
        else:
            difference = len(new_content) - len(wiki_page.content)
            wiki_page.content = new_content
        # Award fiorygi
        if difference > 50:
            fioryg_chance = -(5000/difference) + 100
            fioryg_roll = random.randrange(0, 100)
            if fioryg_roll > fioryg_chance:
                user.fiorygi += 1
        else:
            fioryg_chance = -1
            fioryg_roll = -2
        edit_reason = request.form.get("reason")
        new_log = db.WikiLog(editor=user, edited_key=key, timestamp=datetime.datetime.now(), reason=edit_reason)
        db_session.add(new_log)
        db_session.commit()
        try:
            telegram_bot.send_message(config["Telegram"]["main_group"],
                                      f'ℹ️ La pagina wiki <a href="https://ryg.steffo.eu/wiki/{key}">{key}</a> è stata'
                                      f' modificata da'
                                      f' <a href="https://ryg.steffo.eu/profile/{user.username}">{user.username}</a>'
                                      f' {"(" + edit_reason + ")" if edit_reason else ""}'
                                      f' [{"+" if difference > 0 else ""}{difference}]\n'
                                      f' {"<b>" + user.username + " è stato premiato con 1 fioryg!</b>" if fioryg_roll > fioryg_chance else ""}',
                                      parse_mode="HTML", disable_web_page_preview=True, disable_notification=True)
        except Exception:
            pass
        return redirect(url_for("page_wiki", key=key))


@app.route("/diario")
def page_diario():
    user_id = fl_session.get("user_id")
    if not user_id:
        return redirect(url_for("page_login"))
    db_session = db.Session()
    diario_entries = db_session.query(db.Diario).order_by(db.Diario.timestamp.desc()).all()
    db_session.close()
    return render_template("diario.html", g=fl_g, entries=diario_entries)


@app.route("/api/token")
def api_token():
    username = request.form.get("username", "")
    password = request.form.get("password", "")
    db_session = db.Session()
    user = db_session.query(db.Royal).filter_by(username=username).one_or_none()
    if user is None:
        db_session.close()
        abort(403)
        return
    if user.password is None:
        db_session.close()
        abort(403)
    if bcrypt.checkpw(bytes(password, encoding="utf8"), user.password):
        new_token = db.LoginToken(royal=user, token=secrets.token_urlsafe())
        db_session.add(new_token)
        db_session.commit()
        db_session.close()
        return jsonify({
            "id": user.id,
            "username": user.username,
            "token": new_token.token
        })
    else:
        abort(403)
        return


@app.route("/ses/identify")
def ses_identify():
    response = jsonify({
        "username": fl_session.get("username"),
        "id": fl_session.get("user_id")
    })
    response.headers["Access-Control-Allow-Origin"] = "http://lvh.me:1234"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    return response


@app.before_request
def pre_request():
    fl_g.event_started, fl_g.event_progress = db.Halloween.puzzle_status()
    fl_g.time_left = datetime.datetime.fromtimestamp(1540999800) - datetime.datetime.now()
    fl_g.display_on_main_site = (fl_g.time_left < datetime.timedelta(days=7)) or __debug__
    fl_g.css = "spoopy.less" if (fl_g.event_started or __debug__) else "nryg.less"
    fl_g.rygconf = config


if __name__ == "__main__":
    try:
        app.run(host="0.0.0.0", port=1235, debug=__debug__)
    except KeyboardInterrupt:
        pass
