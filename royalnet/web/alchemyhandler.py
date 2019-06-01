import flask as f
from werkzeug.local import LocalProxy


alchemy = f.current_app.config["ALCHEMY"]


def get_alchemy_session():
    if "alchemy_session" not in f.g:
        f.g.alchemy_session = alchemy.Session()
    return f.g.alchemy_session


@f.current_app.teardown_appcontext
def teardown_alchemy_session(*_, **__):
    _alchemy_session = f.g.pop("alchemy_session", None)
    if _alchemy_session is not None:
        _alchemy_session.close()


alchemy_session = LocalProxy(get_alchemy_session)
