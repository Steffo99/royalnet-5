import os
from .web import create_app
from .web.blueprints import home, wikiview, tglogin


class TestConfig:
    DB_PATH = os.environ["DB_PATH"]


app = create_app(TestConfig, [home, wikiview, tglogin])


if __name__ == "__main__":
    app.run()
