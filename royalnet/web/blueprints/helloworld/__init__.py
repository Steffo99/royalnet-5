import flask as f
from ... import Royalprint


bp = Royalprint("helloworld", __name__, url_prefix="/helloworld")


@bp.route("/")
def helloworld_index():
    return "Hello world!"
