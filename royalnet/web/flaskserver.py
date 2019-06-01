import typing
import flask as f
from ..database import Alchemy


def create_app(config_obj: typing.Type, blueprints: typing.List[f.Blueprint]):
    app = f.Flask(__name__)
    app.config.from_object(config_obj)
    with app.app_context():
        f.g.alchemy = Alchemy(app.config["DB_PATH"], app.config["REQUIRED_TABLES"])
    for blueprint in blueprints:
        app.register_blueprint(blueprint)
    return app
