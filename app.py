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
            db_session().flush() # Flush so sqlalchemy populates our game variable with id

            # Add the creator as a player
            player = Players(game_id=game.id,
                    user_id=creator)
            db_session().add(player)
            db_session().commit()

            return redirect(url_for('game', game=game.id))

    return redirect(url_for('index'))

@app.route("/games/<game>")
def game(game=None):
    if session['user'] is not None:
        user_is_spy = db_session.query(Players.is_spy).join(Users).filter(Players.game_id == game).filter(Users.id == session['user']).scalar()
    players = db_session.query(Users.name, Players).join(Players).filter(Players.game_id == game).all()
    posts = db_session.query(Users.name, Posts).join(Posts).filter(Posts.game_id == game).all()
    return render_template("game.html", players=players, posts=posts, game=game, user_is_spy=user_is_spy)

@app.route("/games/<game>/missions")
def missions(game=None):
    # order_by id so missions[0] is the first one, missions[1] is the second one and so on.
    missions = db_session.query(Missions).join(Games) \
        .filter(Games.id == game).order_by(Missions.id.asc()).all()

    for mission in missions:
        # order_by id so turns[0] is the first one, turns[1] is the second one and so on.
        turns = db_session.query(Turns) \
            .filter(Turns.mission_id == mission.id).order_by(Turns.id.asc()).all()
        for turn in turns:
            turn_votes = db_session.query(Users.name, TurnVotes.approve).select_from(TurnVotes) \
                    .join(Players).join(Users).filter(TurnVotes.turn_id==turn.id).all()
            turn.votes = turn_votes

            nominees = db_session.query(Users.name).join(Players).join(Nominees).filter(Nominees.turn_id == turn.id).all()
            turn.nominees = nominees

        mission_votes = db_session.query(Users.name, MissionVotes.fail).select_from(MissionVotes) \
                .join(Players).join(Users).filter(MissionVotes.mission_id == mission.id).all()
        mission.votes = mission_votes
        mission.turns = turns

    game = db_session.query(Games).filter(Games.id == game).scalar()
    return render_template('missions.html', missions=missions, game=game)




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
