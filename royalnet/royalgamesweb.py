import os
from .web import create_app
from .web.royalprints import rp_home, rp_wikiview, rp_tglogin, rp_docs


class TestConfig:
    DB_PATH = os.environ["DB_PATH"]
    TG_AK = os.environ["TG_AK"]


app = create_app(TestConfig, [rp_home, rp_wikiview, rp_tglogin, rp_docs])


if __name__ == "__main__":
    app.run()
