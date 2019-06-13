"""Quick docs link :py:class:`royalnet.web.Royalprint`."""
import flask as f
from ... import Royalprint


rp = Royalprint("docs", __name__, url_prefix="/docs")


@rp.route("/")
def home_index():
    return f.redirect("https://royal-games.github.io/royalnet/html/index.html")
