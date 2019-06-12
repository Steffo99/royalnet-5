import typing
import flask as f
import os
from sqlalchemy.orm import scoped_session
from ..database import Alchemy
from .royalprint import Royalprint


def create_app(config_obj: typing.Type, blueprints: typing.List[Royalprint]):
    app = f.Flask(__name__)
    app.config.from_object(config_obj)
    app.secret_key = os.environ["SECRET_KEY"]

    @app.teardown_request
    def teardown_alchemy_session(*_, **__):
        alchemy_session = app.config["ALCHEMY_SESSION"]
        if alchemy_session is not None:
            alchemy_session.remove()

    # Load blueprints
    required_tables = set()
    for blueprint in blueprints:
        required_tables = required_tables.union(blueprint.required_tables)
        app.register_blueprint(blueprint)

    # Init Alchemy
    # Seems like a dirty hack to me, but experiments are fun, right?
    if len(required_tables) > 0:
        alchemy = Alchemy(app.config["DB_PATH"], required_tables)
        app.config["ALCHEMY"] = alchemy
        app.config["ALCHEMY_SESSION"] = scoped_session(alchemy.Session)
    else:
        app.config["ALCHEMY"] = None
        app.config["ALCHEMY_SESSION"] = None
    return app
