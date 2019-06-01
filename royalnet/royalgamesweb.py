import os
from .web import create_app
from .web.blueprints import helloworld, testing


class TestConfig:
    DB_PATH = os.environ["DB_PATH"]
    REQUIRED_TABLES = set()


app = create_app(TestConfig, [helloworld, testing])


if __name__ == "__main__":
    app.run()
