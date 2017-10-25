from flask import Flask, render_template
from db import session, Session, Royal, Steam, RocketLeague, Dota, Osu, Overwatch, LeagueOfLegends

app = Flask(__name__)

app.jinja_env.trim_blocks = True
app.jinja_env.lstrip_blocks = True

@app.route("/leaderboards")
def page_leaderboards():
    dota_data = session.query(Dota).join(Steam).join(Royal).all()
    rl_data = session.query(RocketLeague).join(Steam).join(Royal).all()
    ow_data = session.query(Overwatch).join(Royal).all()
    osu_data = session.query(Osu).join(Royal).all()
    lol_data = session.query(LeagueOfLegends).join(Royal).all()
    return render_template("leaderboards.html", dota_data=dota_data, rl_data=rl_data, ow_data=ow_data, osu_data=osu_data, lol_data=lol_data)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=1234, debug=True)
    session.close()