import flask as f
from ... import Royalprint
from ....database.tables import Royal


bp = Royalprint("testing", __name__, url_prefix="/testing", required_tables={Royal})


@bp.route("/listroyals")
def testing_listroyals():
    from ...alchemyhandler import alchemy, alchemy_session
    royals = alchemy_session.query(alchemy.Royal).all()
    return f'<body><script type="text/plain" style="display: block;">{repr(royals)}</script></body>'
