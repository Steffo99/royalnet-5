import typing
import flask as f
from ..database import Alchemy
from .royalprint import Royalprint


def create_app(config_obj: typing.Type, blueprints: typing.List[Royalprint]):
    app = f.Flask(__name__)
    app.config.from_object(config_obj)
    required_tables = set()
    for blueprint in blueprints:
        required_tables = required_tables.union(blueprint.required_tables)
        app.register_blueprint(blueprint)
    app.config["ALCHEMY"] = Alchemy(app.config["DB_PATH"], required_tables)
    return app
