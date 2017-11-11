from flask import Flask, render_template
from db import Session, Royal, Steam, RocketLeague, Dota, Osu, Overwatch, LeagueOfLegends
from sqlalchemy.orm import joinedload
from sqlalchemy import func

app = Flask(__name__)

app.jinja_env.trim_blocks = True
app.jinja_env.lstrip_blocks = True

@app.route("/leaderboards")
def page_leaderboards():
    session = Session()
    dota_data = session.query(Dota).options(joinedload(Dota.steam).joinedload(Steam.royal)).join(Steam).join(Royal).all()
    rl_data = session.query(RocketLeague).options(joinedload(RocketLeague.steam).joinedload(Steam.royal)).join(Steam).join(Royal).all()
    ow_data = session.query(Overwatch).options(joinedload(Overwatch.royal)).join(Royal).all()
    osu_data = session.query(Osu).options(joinedload(Osu.royal)).join(Royal).all()
    lol_data = session.query(LeagueOfLegends).options(joinedload(LeagueOfLegends.royal)).join(Royal).all()
    session.close()
    return render_template("leaderboards.html", dota_data=dota_data, rl_data=rl_data, ow_data=ow_data, osu_data=osu_data, lol_data=lol_data)


if __name__ == "__main__":
    try:
        app.run(host="0.0.0.0", port=1234, debug=True)
    except KeyboardInterrupt:
        pass