from flask import Flask, render_template, request, abort, redirect, url_for, Markup, escape, jsonify
from flask import session as fl_session
from flask import g as fl_g
import db
import bcrypt
import configparser
import markdown2
import datetime
# noinspection PyPackageRequirements
import telegram
import sql_queries
import random
import re
import functools
import strings
from sqlalchemy.orm.collections import InstrumentedList
from raven.contrib.flask import Sentry

app = Flask(__name__)

app.jinja_env.trim_blocks = True
app.jinja_env.lstrip_blocks = True

config = configparser.ConfigParser()
config.read("config.ini")

app.secret_key = config["Flask"]["secret_key"]

telegram_bot = telegram.Bot(config["Telegram"]["bot_token"])

sentry = Sentry(app, dsn=config["Sentry"]["token"])


@app.template_filter()
def markdown(text):
    """Convert a string to markdown."""
    converted_md = markdown2.markdown(text.replace("<", "&lt;"),
                                      extras=["spoiler", "tables", "smarty-pants", "fenced-code-blocks"])
    converted_md = re.sub(r"{https?://(?:www\.)?(?:youtube\.com/watch\?.*?&?v=|youtu.be/)([0-9A-Za-z-]+).*?}",
                          r'<div class="youtube-embed">'
                          r'   <iframe src="https://www.youtube-nocookie.com/embed/\1?rel=0&amp;showinfo=0"'
                          r'           frameborder="0"'
                          r'           allow="autoplay; encrypted-media"'
                          r'           allowfullscreen'
                          r'           width="640px"'
                          r'           height="320px">'
                          r'   </iframe>'
                          r'</div>', converted_md)
    converted_md = re.sub(r"{https?://clyp.it/([a-z0-9]+)}",
                          r'<div class="clyp-embed">'
                          r'    <iframe width="100%" height="160" src="https://clyp.it/\1/widget" frameborder="0">'
                          r'    </iframe>'
                          r'</div>', converted_md)
    return Markup(converted_md)


def require_login(f):
    @functools.wraps(f)
    def func(*args, **kwargs):
        if not fl_g.user:
            abort(403)
            return
        return f(*args, **kwargs)
    return func


@app.errorhandler(400)
def error_400(_=None):
    return render_template("400.html")


@app.route("/400")
def page_400():
    return error_400()


@app.errorhandler(403)
def error_403(_=None):
    return render_template("403.html")


@app.route("/403")
def page_403():
    return error_403()


@app.errorhandler(500)
def error_500(_=None):
    return render_template("500.html")


@app.route("/500")
def page_500():
    return error_500()


@app.route("/")
def page_main():
    royals = fl_g.session.query(db.Royal).order_by(db.Royal.fiorygi.desc()).all()
    wiki_pages = fl_g.session.query(db.WikiEntry).order_by(db.WikiEntry.key).all()
    random_diario = fl_g.session.query(db.Diario).order_by(db.func.random()).first()
    next_events = fl_g.session.query(db.Event).filter(db.Event.time > datetime.datetime.now()).order_by(
        db.Event.time).all()
    quests = fl_g.session.query(db.Quest).all()
    return render_template("main.html", royals=royals, wiki_pages=wiki_pages, entry=random_diario,
                           events=next_events, escape=escape, quests=quests)


@app.route("/profile/<name>")
def page_profile(name: str):
    user = fl_g.session.query(db.Royal).filter_by(username=name).one_or_none()
    if user is None:
        abort(404)
        return
    css = fl_g.session.query(db.ProfileData).filter_by(royal=user).one_or_none()
    mini_data = []
    for game in db.mini_list:
        # TODO: investigate on why instrumentedlists are returned, or minis are not found
        try:
            data = game.mini_get_single_from_royal(fl_g.session, user)
        except Exception:
            data = None
        if data is None:
            continue
        elif isinstance(data, InstrumentedList):
            if len(data) == 0:
                continue
            mini_data.append({
                "name": game._mini_name,
                "data": data[0]
            })
            continue
        mini_data.append({
            "name": game._mini_name,
            "data": data
        })
    if css is not None:
        converted_bio = Markup(markdown2.markdown(css.bio.replace("<", "&lt;"),
                               extras=["spoiler", "tables", "smarty-pants", "fenced-code-blocks"]))
    else:
        converted_bio = ""
    return render_template("profile.html", ryg=user, css=css, bio=converted_bio, mini_data=mini_data)


@app.route("/login")
def page_login():
    return render_template("login.html")


@app.route("/loggedin", methods=["POST"])
def page_loggedin():
    username = request.form.get("username", "")
    password = request.form.get("password", "")
    user = fl_g.session.query(db.Royal).filter_by(username=username).one_or_none()
    fl_session.permanent = True
    if user is None:
        abort(400)
        return
    if user.password is None:
        fl_session["user_id"] = user.id
        fl_session["username"] = username
        return redirect(url_for("page_password"))
    if bcrypt.checkpw(bytes(password, encoding="utf8"), user.password):
        fl_session["user_id"] = user.id
        fl_session["username"] = username
        return redirect(url_for("page_main"))
    return redirect(url_for("page_login"))


@app.route("/logout")
def page_logout():
    if "user_id" in fl_session:
        del fl_session["user_id"]
        del fl_session["username"]
    return redirect(url_for("page_main"))


@app.route("/password", methods=["GET", "POST"])
@require_login
def page_password():
    if request.method == "GET":
        return render_template("password.html")
    elif request.method == "POST":
        new_password = request.form.get("new", "")
        user = fl_g.session.query(db.Royal).filter_by(id=fl_g.user.id).one()
        if user.password is None:
            user.fiorygi += 1
        user.password = bcrypt.hashpw(bytes(new_password, encoding="utf8"), bcrypt.gensalt())
        fl_g.session.commit()
        return redirect(url_for("page_main"))


@app.route("/editprofile", methods=["GET", "POST"])
@require_login
def page_editprofile():
    royal = fl_g.session.query(db.Royal).filter_by(id=fl_g.user.id).one()
    profile_data = fl_g.session.query(db.ProfileData).filter_by(royal=royal).one_or_none()
    if request.method == "GET":
        return render_template("profileedit.html", royal=royal, data=profile_data)
    elif request.method == "POST":
        css = request.form.get("css", "")
        bio = request.form.get("bio", "")
        if "</style" in css:
            abort(400)
            return
        if profile_data is None:
            profile_data = db.ProfileData(royal=royal, css=css, bio=bio)
            fl_g.session.add(profile_data)
            fl_g.session.flush()
        else:
            profile_data.css = css
            profile_data.bio = bio
        fl_g.session.commit()
        return redirect(url_for("page_profile", name=royal.username))


@app.route("/game/<name>")
def page_game(name: str):
    for game in db.mini_list:
        if game._mini_name == name:
            query = game.mini_get_all(fl_g.session)
            break
    else:
        abort(404)
        return
    return render_template("game.html", mini_type=game, mini_data=query)


@app.route("/wiki/<key>")
def page_wiki(key: str):
    wiki_page = fl_g.session.query(db.WikiEntry).filter_by(key=key).one_or_none()
    wiki_latest_edit = fl_g.session.query(db.WikiLog).filter_by(edited_key=key) \
        .order_by(db.WikiLog.timestamp.desc()).first()
    if wiki_page is None:
        return render_template("wikipage.html", key=key, wiki_page=None)
    # Embed YouTube videos
    converted_md = markdown2.markdown(wiki_page.content.replace("<", "&lt;"),
                                      extras=["spoiler", "tables", "smarty-pants", "fenced-code-blocks"])
    converted_md = re.sub(r"{https?://(?:www\.)?(?:youtube\.com/watch\?.*?&?v=|youtu.be/)([0-9A-Za-z-]+).*?}",
                          r'<div class="youtube-embed">'
                          r'   <iframe src="https://www.youtube-nocookie.com/embed/\1?rel=0&amp;showinfo=0"'
                          r'           frameborder="0"'
                          r'           allow="autoplay; encrypted-media"'
                          r'           allowfullscreen'
                          r'           width="640px"'
                          r'           height="320px">'
                          r'   </iframe>'
                          r'</div>', converted_md)
    converted_md = re.sub(r"{https?://clyp.it/([a-z0-9]+)}",
                          r'<div class="clyp-embed">'
                          r'    <iframe width="100%" height="160" src="https://clyp.it/\1/widget" frameborder="0">'
                          r'    </iframe>'
                          r'</div>', converted_md)
    return render_template("wikipage.html", key=key, wiki_page=wiki_page, converted_md=Markup(converted_md),
                           wiki_log=wiki_latest_edit)


@app.route("/wiki/<key>/edit", methods=["POST"])
@require_login
def page_wiki_edit(key: str):
    wiki_page = fl_g.session.query(db.WikiEntry).filter_by(key=key).one_or_none()
    if wiki_page is not None and wiki_page.locked:
        abort(403)
        return
    new_content = request.form.get("content")
    # Create new page
    if wiki_page is None:
        difference = len(new_content)
        wiki_page = db.WikiEntry(key=key, content=new_content)
        fl_g.session.add(wiki_page)
        fl_g.session.flush()
    # Edit existing page
    else:
        difference = len(new_content) - len(wiki_page.content)
        wiki_page.content = new_content
    # Award fiorygi
    if difference > 50:
        fioryg_chance = -(5000/difference) + 100
        fioryg_roll = random.randrange(0, 100)
        if fioryg_roll > fioryg_chance:
            fl_g.user.fiorygi += 1
    else:
        fioryg_chance = -1
        fioryg_roll = -2
    edit_reason = request.form.get("reason")
    new_log = db.WikiLog(editor=fl_g.user, edited_key=key, timestamp=datetime.datetime.now(), reason=edit_reason)
    fl_g.session.add(new_log)
    fl_g.session.commit()
    message = f'ℹ️ La pagina wiki <a href="https://ryg.steffo.eu/wiki/{key}">{key}</a> è stata' \
              f' modificata da' \
              f' <a href="https://ryg.steffo.eu/profile/{fl_g.user.username}">{fl_g.user.username}</a>' \
              f' {"(" + edit_reason + ")" if edit_reason else ""}' \
              f' [{"+" if difference > 0 else ""}{difference}]\n'
    if fioryg_roll > fioryg_chance:
        message += f"⭐️ {fl_g.user.username} è stato premiato con 1 fioryg per la modifica!"
    try:
        telegram_bot.send_message(config["Telegram"]["main_group"], message,
                                  parse_mode="HTML", disable_web_page_preview=True, disable_notification=True)
    except Exception:
        pass
    return redirect(url_for("page_wiki", key=key))


@app.route("/wiki/<key>/lock", methods=["POST"])
@require_login
def page_wiki_lock(key: str):
    wiki_page = fl_g.session.query(db.WikiEntry).filter_by(key=key).one_or_none()
    if wiki_page is None:
        abort(404)
        return
    if fl_g.user.role != "Admin":
        abort(403)
        return
    wiki_page.locked = not wiki_page.locked
    try:
        if wiki_page.locked:
            telegram_bot.send_message(config["Telegram"]["main_group"],
                                      strings.safely_format_string(strings.WIKI.PAGE_LOCKED,
                                                                   key=key,
                                                                   user=fl_g.user.username),
                                      parse_mode="HTML",
                                      disable_web_page_preview=True,
                                      disable_notification=True)
        else:
            telegram_bot.send_message(config["Telegram"]["main_group"],
                                      strings.safely_format_string(strings.WIKI.PAGE_UNLOCKED,
                                                                   key=key,
                                                                   user=fl_g.user.username),
                                      parse_mode="HTML",
                                      disable_web_page_preview=True,
                                      disable_notification=True)
    except Exception:
        pass
    fl_g.session.commit()
    return redirect(url_for("page_wiki", key=key))


@app.route("/diario")
@require_login
def page_diario():
    diario_entries = fl_g.session.query(db.Diario).order_by(db.Diario.timestamp.desc()).all()
    return render_template("diario.html", entries=diario_entries)


@app.route("/music")
def page_music():
    songs = fl_g.session.execute(sql_queries.top_songs)
    return render_template("topsongs.html", songs=songs)


@app.route("/music/<discord_id>")
def page_music_individual(discord_id: str):
    discord = fl_g.session.query(db.Discord).filter_by(discord_id=discord_id).one_or_none()
    if discord is None:
        abort(404)
        return
    songs = fl_g.session.execute(sql_queries.single_top_songs, {"discordid": discord.discord_id})
    return render_template("topsongs.html", songs=songs, discord=discord)


@app.route("/activity")
def page_activity():
    reports = list(fl_g.session.query(db.ActivityReport).order_by(db.ActivityReport.timestamp.desc()).limit(192).all())
    hourly_avg = list(fl_g.session.execute(sql_queries.activity_by_hour))
    return render_template("activity.html", activityreports=list(reversed(reports)), hourly_avg=hourly_avg)


@app.route("/ses/identify")
def ses_identify():
    response = jsonify({
        "username": fl_session.get("username"),
        "id": fl_session.get("user_id")
    })
    response.headers["Access-Control-Allow-Origin"] = "https://steffo.eu"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    return response


@app.route("/hooks/github", methods=["POST"])
def hooks_github():
    try:
        j = request.get_json()
    except Exception:
        abort(400)
        return
    if j is None:
        abort(400)
        return
    # TODO: add secret check
    message = f"🐙 Nuovi aggiornamenti a Royalnet:\n"
    for commit in j.get("commits", []):
        if commit["distinct"]:
            message += f'<a href="{commit["url"]}">{commit["message"]}</a>' \
                       f' di <b>{commit["author"].get("username", "anonimo")}</b>\n'
    telegram_bot.send_message(config["Telegram"]["main_group"], message,
                              parse_mode="HTML", disable_web_page_preview=True, disable_notification=True)
    return "Done."


@app.before_request
def pre_request():
    fl_g.css = "nryg.less"
    fl_g.rygconf = config
    fl_g.session = db.Session()
    try:
        fl_g.user = fl_g.session.query(db.Royal).filter_by(id=fl_session["user_id"]).one_or_none()
    except KeyError:
        fl_g.user = None


@app.after_request
def after_request(response):
    fl_g.session.close()
    return response


if __name__ == "__main__":
    try:
        app.run(host="0.0.0.0", port=1235, debug=__debug__)
    except KeyboardInterrupt:
        pass
