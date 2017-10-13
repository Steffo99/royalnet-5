import db
from flask import Flask, render_template

app = Flask(__name__)

@app.route("/ladder")
def page_dota_ladder():
    session = db.Session()
    dota = session.execute("SELECT royals.username, dota.solo_mmr, dota.party_mmr, dota.wins FROM royals JOIN steam ON royals.id = steam.royal_id JOIN dota ON steam.steam_id = dota.steam_id ORDER BY dota.solo_mmr DESC;")
    rl = session.execute("SELECT royals.username, "
                         "rocketleague.single_rank, rocketleague.single_div, rocketleague.single_mmr, "
                         "rocketleague.doubles_rank, rocketleague.doubles_div, rocketleague.doubles_mmr, "
                         "rocketleague.standard_rank, rocketleague.standard_div, rocketleague.standard_mmr, "
                         "rocketleague.solo_std_rank, rocketleague.solo_std_div, rocketleague.solo_std_mmr "
                         "FROM royals JOIN steam ON royals.id = steam.royal_id "
                         "JOIN rocketleague ON steam.steam_id = rocketleague.steam_id "
                         "ORDER BY rocketleague.doubles_rank DESC;")
    osu = session.execute("SELECT royals.username, osu.std_pp, osu.taiko_pp, osu.catch_pp, osu.mania_pp FROM royals JOIN osu ON royals.id = osu.royal_id ORDER BY osu.std_pp DESC;")
    return render_template("main.htm", dota=dota, rl=rl, osu=osu)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=1234)