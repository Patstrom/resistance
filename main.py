from flask import Flask
from flask import render_template
from flask import abort
app = Flask(__name__)

from post import Post

games = ["2002", "2102", "dafs2", "agjl"]
players = ["jozzter", "karlszone", "idris", "joakim", "fredrika.agestam & alex.loiko",
        "benjamin", "simon"]

posts = []
for player in players:
    posts.append(Post(player, "{} says hi".format(player)))

@app.route("/")
def index():
    return render_template("index.html", games=games)

@app.route("/games/<game>")
def game(game=None):
    if game in games:
        return render_template("game.html", players=players, posts=posts)
    else:
        return render_template("404.html"), 404

@app.errorhandler(404)
def page_not_found(error):
    return render_template("404.html"), 404


if __name__ == "__main__":
    app.run()
