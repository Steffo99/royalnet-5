import flask as f
import os
from ..database import Alchemy


app = f.Flask(__name__)
app.config["RN_ALCHEMY"] = Alchemy(os.environ["DB_PATH"], set())
with app.app_context():
    from .alchemyhandler import alchemy_session as db_session


@app.route("/")
def test():
    ...
    return repr(db_session)


if __name__ == "__main__":
    app.run()
