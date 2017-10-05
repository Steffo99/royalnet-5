from flask import Flask
from flask import session as flask_session
from flask_openid import OpenID
from db import session, Royal, Steam
import requests
import re

# Init the config reader
import configparser
config = configparser.ConfigParser()
config.read("config.ini")

# Init Flask and Flask_OpenID
app = Flask(__name__)
app.secret_key = config["Steam"]["secret_key"]
oid = OpenID(app)

@app.route("/login/<int:royal_id>")
@oid.loginhandler
def page_steam_login(royal_id):
    flask_session["royal_id"] = royal_id
    return oid.try_login("http://steamcommunity.com/openid")


@oid.after_login
def page_after_login(response):
    steam_id = re.search("https?://steamcommunity\.com/openid/id/(.+)", response.identity_url).group(1)
    db_steam = session.query(Steam).filter(Steam.steam_id == steam_id).first()
    if db_steam is None:
        db_steam = Steam(royal_id=flask_session["royal_id"],
                         steam_id=steam_id)
        session.add(db_steam)
        db_steam.update()
        session.commit()
        return "Account Steam collegato con successo!"
    else:
        return "Il tuo account Steam è già collegato."


@app.route("/update/<int:royal_id>")
def page_steam_update(royal_id):
    db_steam = session.query(Steam).filter(Steam.royal_id == royal_id).first()
    db_steam.update()
    return "Dati account aggiornati."


if __name__ == "__main__":
    app.run(host="0.0.0.0", port="1234")