import flask as f
from .. import Royalprint
from ...database.tables import Royal


bp = Royalprint("helloworld", __name__, url_prefix="/helloworld", required_tables={Royal})


@bp.route("/")
def helloworld():
    royals = f.g.alchemy_session.query(f.g.alchemy.Royal).all()
    return repr(royals)


@bp.before_request
def before_request():
    f.g.alchemy_session = f.g.alchemy.Session()


@bp.after_request
def after_request():
    alchemy_session = f.g.pop("alchemy_session", None)
    if alchemy_session is not None:
        alchemy_session.close()
