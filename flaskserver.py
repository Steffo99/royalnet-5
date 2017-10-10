import db
from flask import Flask, render_template

app = Flask(__name__)

@app.route("/dota/ladder")
def page_dota_ladder():
    session = db.Session()
    query = session.execute("SELECT royals.username, dota.solo_mmr, dota.party_mmr, dota.wins FROM royals JOIN steam ON royals.id = steam.royal_id JOIN dota ON steam.steam_id = dota.steam_id ORDER BY dota.solo_mmr DESC;")
    return render_template("table.htm", query=query)


@app.route("/rl/ladder")
def page_rl_ladder():
    session = db.Session()
    query = session.execute("SELECT royals.username, rocketleague.single_mmr, rocketleague.doubles_mmr, rocketleague.standard_mmr, rocketleague.solo_std_mmr FROM royals JOIN steam ON royals.id = steam.royal_id JOIN rocketleague ON steam.steam_id = rocketleague.steam_id ORDER BY rocketleague.doubles_mmr DESC;")
    return render_template("table.htm", query=query)


@app.route("/osu/ladder")
def page_osu_ladder():
    session = db.Session()
    query = session.execute("SELECT royals.username, osu.std_pp, osu.taiko_pp, osu.catch_pp, osu.mania_pp FROM royals JOIN osu ON royals.id = osu.royal_id ORDER BY osu.std_pp DESC;")
    return render_template("table.htm", query=query)



if __name__ == "__main__":
    app.run()