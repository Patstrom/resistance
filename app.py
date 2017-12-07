from flask import Flask
from flask import render_template
from flask import abort

app = Flask(__name__)
app.config.from_envvar('FLASK_ENV_FILE')

from database import load_session
db_session = load_session()
from models import *

@app.route("/")
def index():
    games = db_session.query(Games).all()
    return render_template("index.html", games=games, usergames=games)

@app.route("/games/<game>")
def game(game=None):
    players = db_session.query(Players).filter(Players.game_id == game).all()
    posts = db_session.query(Posts).filter(Posts.game_id == game).all()
    return render_template("game.html", players=players, posts=posts)

@app.errorhandler(404)
def page_not_found(error):
    return render_template("404.html"), 404

@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()

if __name__ == "__main__":
    app.run()
