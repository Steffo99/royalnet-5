import flask as f
import werkzeug.local


def get_alchemy_session():
    if "alchemy_session" not in f.g:
        f.g.alchemy_session = f.current_app.config["RN_ALCHEMY"].Session()
    return f.g.alchemy_session


@f.current_app.teardown_appcontext
def teardown_alchemy_session(*args, **kwargs):
    _alchemy_session = f.g.pop("alchemy_session", None)
    if _alchemy_session is not None:
        _alchemy_session.close()


alchemy_session = werkzeug.local.LocalProxy(get_alchemy_session)
