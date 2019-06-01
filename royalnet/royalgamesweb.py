import os
from .web import create_app
from .web.blueprints import home


class TestConfig:
    DB_PATH = os.environ["DB_PATH"]
    REQUIRED_TABLES = set()


app = create_app(TestConfig, [home])


if __name__ == "__main__":
    app.run()
