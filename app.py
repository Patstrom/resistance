from flask import Flask, session, request, redirect, url_for
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
    if 'user' in session:
        user = session['user']
        usergames = db_session.query(Games).join(Players).filter(Players.user_id == user).all()
        return render_template('index_for_users.html', games=games, usergames=usergames)
    else:
        return render_template("index_for_anonymous.html", games=games)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = db_session.query(Users).filter(Users.name == username).scalar()

        # Check if login is successful
        if user is not None and user.check_password(password):
            session['user'] = user.id
            return redirect(url_for('index'))
        else:
            return render_template("login.html", failed=True)
    else:
        return render_template("login.html", failed=False)

@app.route("/logout")
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

@app.route("/create-game", methods=["GET", "POST"])
def create_game():
    if request.method == "GET":
        return redirect(url_for('index'))
    else:
        creator = session.get('user')
        name = request.form["game-name"]
        if creator is not None and not name.isspace():
            # Create the game
            game = Games(creator=creator,
                    name = name)
            db_session().add(game)
            db_session().flush()

            # Add the creator as a player
            player = Players(game_id=game.id,
                    user_id=creator)
            db_session().add(player)
            db_session().commit()

            return redirect(url_for('game', game=game.id))

    return redirect(url_for('index'))

@app.route("/games/<game>")
def game(game=None):
    players = db_session.query(Users.name, Players).join(Players).filter(Players.game_id == game).all()
    posts = db_session.query(Users.name, Posts).join(Posts).filter(Posts.game_id == game).all()
    return render_template("game.html", players=players, posts=posts, game=game)



@app.route("/games/<game>/submit-post", methods=["GET", "POST"])
def submit_post(game=None):
    if request.method == "GET":
        return redirect(url_for('game', game=game))
    else:
        body = request.form["body"]
        author = session['user']
        current_mission = db_session.query(Missions.id).join(Games).filter(Games.id == game).order_by(Missions.id.desc()).scalar()
        post = Posts(author = author,
                game_id = game,
                mission_id = current_mission,
                body = body)
        db_session().add(post)
        db_session().commit()
        return redirect(url_for('game', game=game))

@app.errorhandler(404)
def page_not_found(error):
    return render_template("404.html"), 404

@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()

if __name__ == "__main__":
    app.run()
