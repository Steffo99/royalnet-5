import typing
import flask as f
from ..database import Alchemy


class RoyalFlask:
    def __init__(self, config_obj: typing.Type):
        self.app = f.Flask(__name__)
        self.app.config.from_object(config_obj)
        self.alchemy = Alchemy(self.app.config["RF_DATABASE_URI"], self.app.config["RF_REQUIRED_TABLES"])
        for blueprint in self.app.config["RF_BLUEPRINTS"]:
            self.app.register_blueprint(blueprint)

    def debug(self):
        self.app.run(host="127.0.0.1", port=1234, debug=True)
