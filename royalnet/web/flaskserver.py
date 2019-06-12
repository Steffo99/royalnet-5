import typing
import flask as f
import os
from sqlalchemy.orm import scoped_session
from ..database import Alchemy
from .royalprint import Royalprint


def create_app(config_obj: typing.Type, blueprints: typing.List[Royalprint]):
    """Create a :py:class:`flask.Flask` application object.

    Gets the ``app.secret_key`` from the ``SECRET_KEY`` envvar.

    Also requires a ``DB_PATH`` key in ``config_obj`` to initialize the database connection.

    Warning:
        The code for this class was written at 1 AM, and I have no clue of how and why it works or even of if it really does work.
        Use with caution?

    Args:
        config_obj: The object to be passed to :py:meth:`flask.Flask.config.from_object`.
        blueprints: A list of blueprints to be registered to the application.

    Returns:
        The created :py:class:`flask.Flask`."""
    app = f.Flask(__name__)
    app.config.from_object(config_obj)
    app.secret_key = os.environ["SECRET_KEY"]

    # Load blueprints
    required_tables = set()
    for blueprint in blueprints:
        required_tables = required_tables.union(blueprint.required_tables)
        app.register_blueprint(blueprint)

    # Init Alchemy
    # Seems like a dirty hack to me, but experiments are fun, right?
    # WARNING BLACK SORCERY BELOW EDIT AT YOUR OWN RISK
    if len(required_tables) > 0:
        alchemy = Alchemy(app.config["DB_PATH"], required_tables)
        app.config["ALCHEMY"] = alchemy
        app.config["ALCHEMY_SESSION"] = scoped_session(alchemy.Session)
    else:
        app.config["ALCHEMY"] = None
        app.config["ALCHEMY_SESSION"] = None

    @app.teardown_request
    def teardown_alchemy_session(*_, **__):
        alchemy_session = app.config["ALCHEMY_SESSION"]
        if alchemy_session is not None:
            alchemy_session.remove()
    # END OF BLACK SORCERY

    return app
