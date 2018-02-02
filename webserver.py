from flask import Flask, render_template
from db import Session, Royal, Steam, RocketLeague, Dota, Osu, Overwatch, LeagueOfLegends, Diario, Telegram

app = Flask(__name__)

app.jinja_env.trim_blocks = True
app.jinja_env.lstrip_blocks = True

@app.route("/")
def page_index():
    return render_template("index.html")

@app.route("/diario")
def page_diario():
    session = Session()
    diario_data = session.query(Diario).outerjoin((Telegram, Diario.author), aliased=True).outerjoin(Royal, aliased=True).outerjoin((Telegram, Diario.saver), aliased=True).outerjoin(Royal, aliased=True).all()
    session.close()
    return render_template("diario.html", diario_data=diario_data)

@app.route("/leaderboards")
def page_leaderboards():
    session = Session()
    dota_data = session.query(Dota).join(Steam).join(Royal).order_by(Dota.rank_tier).all()
    rl_data = session.query(RocketLeague).join(Steam).join(Royal).order_by(RocketLeague.doubles_mmr).all()
    ow_data = session.query(Overwatch).join(Royal).order_by(Overwatch.rank).all()
    osu_data = session.query(Osu).join(Royal).order_by(Osu.std_pp).all()
    lol_data = session.query(LeagueOfLegends).join(Royal).order_by(LeagueOfLegends.summoner_name).all()
    session.close()
    return render_template("leaderboards.html", dota_data=dota_data, rl_data=rl_data, ow_data=ow_data, osu_data=osu_data, lol_data=lol_data)

@app.route("/challenge/1")
def page_challenge_one():
    session = Session()
    result = session.execute(r"SELECT sum(osu.std_pp) + sum(osu.taiko_pp) + sum(osu.catch_pp) + sum(osu.mania_pp) total_pp FROM osu;").first()[0]
    session.close()
    return render_template("challenge1.html", starting=4959.518703999999, result=result, target=5200)


if __name__ == "__main__":
    try:
        app.run(host="0.0.0.0", port=1234)
    except KeyboardInterrupt:
        pass
