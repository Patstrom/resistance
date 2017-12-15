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
        if creator is not None and not name:
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

@app.route("/<game>")
def game(game=None):
    user = session.get('user', None)

    # All players and posts for the current game
    players = db_session.query(Users.name, Players).join(Players).filter(Players.game_id == game).all()
    posts = db_session.query(Users.name, Posts).join(Posts).filter(Posts.game_id == game).all()

    user_is_player = user in [player.user_id for (_, player) in players] # Will be false if use is None
    (creator, game_has_started) = db_session.query(Games.creator, Games.started).filter(Games.id == game).one()
    if not game_has_started:
        return render_template('game_not_started.html', players=players, posts=posts, game=game,
                    user_is_creator=creator == user, user_is_player=user_is_player)


    # The current turn and the nominees
    current_turn = db_session.query(Turns).join(Missions).join(Games).filter(Games.id == game) \
        .order_by(Turns.id.desc()).limit(1).scalar()
    leader = db_session.query(Users.name).join(Players).filter(Players.id == current_turn.leader).scalar()
    nominees = db_session.query(Users.name).join(Players).join(Nominees) \
            .filter(Nominees.turn_id == current_turn.id).all()


    # Check if the visitor is logged in and is part of the game
    if user_is_player:
        user_is_spy = db_session.query(Players.is_spy).join(Users).filter(Players.game_id == game).filter(Users.id == user).scalar()
        user_is_leader = True if session['user'] == current_turn.leader else False
        players_required = db_session.query(Missions.people_required).join(Turns).filter(Turns.id == current_turn.id).scalar()

        return render_template("game_for_players.html", players=players, posts=posts,
                game=game, nominees=nominees, leader=leader,
                user_is_spy=user_is_spy, user_is_leader=user_is_leader, players_required=players_required)

    return render_template("game_for_anonymous.html", players=players, posts=posts,
            game=game, nominees=nominees, leader=leader)

@app.route("/games/<game>/join-game", methods=["GET", "POST"])
def join_game(game=None):
    if request.method == "POST":
        user = session.get('user', None)
        # If not logged in redirect to login page
        if user is None:
            return redirect(url_for('login'))

        players = db_session.query(Players).filter(Players.game_id == game).all()
        user_is_player = user in [player.user_id for player in players]

        # This check isn't neccesary if the user behaves
        if not user_is_player:
            player = Players(game_id=game, user_id=user)
            db_session().add(player)
            db_session().commit()

    return redirect(url_for('game', game=game))

@app.route("/games/<game>/start-game", methods=["GET", "POST"])
def start_game(game=None):
    if request.method == "POST":
        # Make sure it's actually the creator that is starting the game
        user = session.get('user', None)
        creator = db_session.query(Games.creator).filter(Games.id == game).scalar()
        if user != creator:
            return redirect(url_for('game', game=game))

        # Get the game's players
        players = db_session.query(Players).filter(Players.game_id == game).all()
        number_of_players = len(players)
        if number_of_players < 5 or number_of_players > 10:
            return redirect(url_for('game', game=game))

        # Choose the spies
        import random
        import resistance_rules
        spies = random.sample(players, number_of_spies[number_of_players])
        for spy in spies:
            spy.is_spy = True
            db_session().merge(spy)

        # Get a leader order
        random.shuffle(players)
        for index, player in enumerate(players):
            db_session().add(LeaderOrder(game_id=game,
                current_leader=player.id,
                next_leader=players[index + 1 % number_of_players]))

        # Create the first mission and turn
        mission = Missions(game_id=game,
            fails_required=1,
            people_required=number_of_players_for_mission[number_of_players][0])
        db_session().add(mission)
        db_session().flush()
        turn = Turns(mission_id=mission.id, leader=players[0].id)
        db_session().add(turn)

        # Set game started to true
        game = db_session.query(Games).filter(Games.id == game).scalar()
        game.started = True
        db_session().merge(game)
        db_session.commit()

    return redirect(url_for('game', game=game))

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

@app.route("/games/<game>/turn-vote", methods=["GET", "POST"])
def turn_vote(game=None):
    if session.get('user', None) is not None:
        if request.method == "POST":
            player_id = db_session.query(Players.id).filter(Players.user_id == session['user'], Players.game_id == game).scalar()
            current_turn = db_session.query(Turns.id).join(Missions).join(Games).filter(Games.id == game) \
                .order_by(Turns.id.desc()).limit(1).scalar()

            approve = False
            if request.form.get('approve', None) is not None:
                approve = True
            vote = TurnVotes(turn_id = current_turn,
                    player_id=player_id,
                    approve=approve)
            db_session().merge(vote)
            db_session().commit()

    return redirect(url_for('game', game=game))



@app.route("/games/<game>/submit-post", methods=["GET", "POST"])
def submit_post(game=None):
    if request.method == "GET":
        return redirect(url_for('game', game=game))
    else:
        body = request.form["body"]
        author = session.get('user', None)
        # If there is no author or body is None or empty then just redirect back
        if author is None or not body:
            return redirect(url_for('game', game=game))

        current_mission = db_session.query(Missions.id).join(Games).filter(Games.id == game) \
                .order_by(Missions.id.desc()).limit(1).scalar()
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
