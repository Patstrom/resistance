from flask import Flask, session, request, redirect, url_for
from flask import render_template
from flask import abort

import random
from resistance_rules import *

app = Flask(__name__)
app.config.from_envvar('FLASK_ENV_FILE')

from database import load_session
db_session = load_session()
from models import *

def check_game(game):
    try:
        if db_session.query(Games).filter(Games.id == game).count() == 0:
            return True
    except:
        return True

    return False

@app.context_processor
def inject_user():
    user = session.get('user', None)
    user_is_logged_in = False if user is None else True
    username = "guest"
    if user_is_logged_in:
        username = db_session.query(Users.name).filter(Users.id == user).scalar()
    return dict(user_is_logged_in=user_is_logged_in, username=username)

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
    # User is already logged in
    if session.get('user', None) is not None:
        return redirect(url_for('index'))

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

@app.route("/signup", methods=["GET", "POST"])
def signup():
    # User is already logged in
    if session.get('user', None) is not None:
        return redirect(url_for('index'))

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = Users(username, password)
        db_session().add(user)
        db_session().commit()
        session['user'] = user.id
        return redirect(url_for('index'))
    else:
        return render_template('signup.html')

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

    if check_game(game):
        return redirect(url_for('index'))

    # All players and posts for the current game
    players = db_session.query(Users.name, Players).join(Players).filter(Players.game_id == game).all()
    posts = db_session.query(Users.name, Posts).join(Posts).filter(Posts.game_id == game).all()

    user_is_player = user in [player.user_id for (_, player) in players] # Will be false if user is None
    (creator, game_has_started) = db_session.query(Games.creator, Games.started).filter(Games.id == game).one()
    creator_name = "".join([name for (name, player) in players if player.user_id==creator])
    if not game_has_started:
        return render_template('game_not_started.html', players=players, posts=posts, game=game,
                    user_is_creator=creator == user, user_is_player=user_is_player,
                    creator_name=creator_name)


    # The current turn and the nominees
    current_turn = db_session.query(Turns).join(Missions).filter(Missions.game_id == game) \
        .order_by(Turns.id.desc()).limit(1).scalar()

    leader = db_session.query(Users.name).join(Players).filter(Players.id == current_turn.leader).scalar()

    nominee_ids = db_session.query(Nominees.player_id) \
            .filter(Nominees.turn_id == current_turn.id).all()
    nominee_ids = [n[0] for n in nominee_ids] # Unpack the result
    nominee_names = [name for (name, player) in players if player.id in nominee_ids]

    # Check if the visitor is logged in and is part of the game
    if user_is_player:
        user_is_spy = db_session.query(Players.is_spy).join(Users).filter(Players.game_id == game).filter(Users.id == user).scalar()
        # Show spies who all spies are
        if user_is_spy:
            players = [(name + " (spy)", player) if player.is_spy else (name, player) for (name, player) in players]

        user_is_leader = user in [player.user_id for (_, player) in players if player.id == current_turn.leader]
        user_is_nominated = user in [player.user_id for (_, player) in players if player.id in nominee_ids]

        # Determine user's vote, if there is one
        user_vote_query = db_session.query(TurnVotes.approve).join(Players) \
                .filter(TurnVotes.turn_id == current_turn.id, Players.user_id == user)
        user_has_voted = user_vote_query.count() > 0
        user_vote = None
        if user_has_voted:
            user_vote = user_vote_query.scalar()

        (players_required, team_is_chosen) = db_session.query(
                Missions.people_required, Missions.team_is_chosen).join(Turns) \
                .filter(Turns.id == current_turn.id).one()

        return render_template("game_for_players.html", players=players, posts=posts,
                game=game, nominees=nominee_names, leader=leader, current_turn=current_turn,
                user_is_spy=user_is_spy, user_is_leader=user_is_leader, players_required=players_required,
                team_is_chosen=team_is_chosen, user_is_nominated=user_is_nominated, user_vote=user_vote)

    return render_template("game_for_anonymous.html", players=players, posts=posts,
            game=game, nominees=nominee_names, leader=leader)

@app.route("/<game>/join-game", methods=["GET", "POST"])
def join_game(game=None):
    if check_game(game):
        return redirect(url_for('index'))

    if request.method == "POST":
        user = session.get('user', None)
        # If not logged in redirect to login page
        if user is None:
            return redirect(url_for('login'))

        players = db_session.query(Players).filter(Players.game_id == game).all()
        user_is_player = user in [player.user_id for player in players]

        # If user hasn't already joined and if there is room
        if not user_is_player or len(players) > 10:
            player = Players(game_id=game, user_id=user)
            db_session().add(player)
            db_session().commit()

    return redirect(url_for('game', game=game))

@app.route("/<game>/start-game", methods=["GET", "POST"])
def start_game(game=None):
    if check_game(game):
        return redirect(url_for('index'))

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
        spies = random.sample(players, number_of_spies[number_of_players])
        for spy in spies:
            spy.is_spy = True
            db_session().merge(spy)

        # Get a leader order
        random.shuffle(players)
        for index, player in enumerate(players):
            db_session().add(LeaderOrder(game_id=game,
                current_leader=player.id,
                next_leader=players[(index + 1) % number_of_players].id))

        # Create the first mission and turn
        mission = Missions(game_id=game,
            fails_required=1,
            people_required=number_of_players_for_mission[number_of_players][0])
        db_session().add(mission)
        db_session().flush()
        turn = Turns(mission_id=mission.id, leader=players[0].id)
        db_session().add(turn)

        # Set game started to true
        game_obj = db_session.query(Games).filter(Games.id == game).scalar()
        game_obj.started = True
        db_session().merge(game_obj)
        db_session.commit()

    return redirect(url_for('game', game=game))

@app.route("/<game>/missions")
def missions(game=None):
    if check_game(game):
        return redirect(url_for('index'))
    # order_by id so missions[0] is the first one, missions[1] is the second one and so on.
    missions = db_session.query(Missions).join(Games) \
        .filter(Games.id == game).order_by(Missions.id.asc()).all()

    for mission in missions:
        # order_by id so turns[0] is the first one, turns[1] is the second one and so on.
        turns = db_session.query(Turns) \
            .filter(Turns.mission_id == mission.id).order_by(Turns.id.asc()).all()
        for turn in turns:
            turn_votes = db_session.query(Users.name, TurnVotes.approve, Players.is_spy).select_from(TurnVotes) \
                    .join(Players).join(Users).filter(TurnVotes.turn_id==turn.id).all()
            turn.votes = turn_votes

            nominees = db_session.query(Users.name, Players.is_spy).join(Players).join(Nominees).filter(Nominees.turn_id == turn.id).all()
            turn.nominees = nominees

        mission_votes = db_session.query(Users.name, MissionVotes.fail, Players.is_spy).select_from(MissionVotes) \
                .join(Players).join(Users).filter(MissionVotes.mission_id == mission.id).all()
        mission.votes = mission_votes
        mission.turns = turns

    game = db_session.query(Games).filter(Games.id == game).scalar()

    # If game is over show who are spies
    if game.is_over:
        for mission in missions:
            for turn in turns:
                turn.votes = [(name+" (spy)", approve) if is_spy else (name, approve) for (name, approve, is_spy) in turn.votes]
                turn.nominees = [name+" (spy)" if is_spy else name for (name, is_spy) in turn.nominees]
            mission.votes = [(name+" (spy)", fail) if is_spy else (name, fail) for (name, fail, is_spy) in mission.votes]
    else:
        for mission in missions:
            for turn in turns:
                turn.votes = [(name, approve) if is_spy else (name, approve) for (name, approve, is_spy) in turn.votes]
                turn.nominees = [name if is_spy else name for (name, is_spy) in turn.nominees]
            mission.votes = [(name, fail) if is_spy else (name, fail) for (name, fail, is_spy) in mission.votes]

    return render_template('missions.html', missions=missions, game=game)

@app.route("/<game>/mission-vote", methods=["GET", "POST"])
def mission_vote(game=None):
    if check_game(game):
        return redirect(url_for('index'))
    if session.get('user', None) is not None:
        if request.method == "POST":
            player_id = db_session.query(Players.id).filter(Players.user_id == session['user'], Players.game_id == game).scalar()
            if player_id is None: # If user isn't part of the game
                return redirect(url_for('game', game=game))

            current_mission = db_session.query(Missions).filter(Missions.game_id == game) \
                    .order_by(Missions.id.desc()).limit(1).scalar()
            if current_mission.is_over or not current_mission.team_is_chosen:
                return redirect(url_for('game', game=game)) # Don't allow voting on an old turn

            fail = False
            if request.form.get('fail', None) is not None:
                fail = True
            vote = MissionVotes(mission_id=current_mission.id,
                    player_id=player_id,
                    fail=fail)
            db_session().merge(vote)
            db_session().commit()

    return redirect(url_for('game', game=game))

@app.route("/<game>/turn-vote", methods=["GET", "POST"])
def turn_vote(game=None):
    if check_game(game):
        return redirect(url_for('index'))
    if session.get('user', None) is not None:
        if request.method == "POST":
            player_id = db_session.query(Players.id).filter(Players.user_id == session['user'], Players.game_id == game).scalar()
            if player_id is None: # If user isn't part of the game
                return redirect(url_for('game', game=game))

            current_mission = db_session.query(Missions).filter(Missions.game_id == game) \
                    .order_by(Missions.id.desc()).limit(1).scalar()
            if current_mission.is_over or current_mission.team_is_chosen:
                return redirect(url_for('game', game=game)) # Don't allow voting on an old turn
            current_turn = db_session.query(Turns.id).filter(Turns.mission_id == current_mission.id) \
                .scalar()

            approve = False
            if request.form.get('approve', None) is not None:
                approve = True
            vote = TurnVotes(turn_id = current_turn,
                    player_id=player_id,
                    approve=approve)
            db_session().merge(vote)
            db_session().commit()

    return redirect(url_for('game', game=game))

@app.route("/<game>/nominate", methods=["GET", "POST"])
def nominate(game=None):
    if check_game(game):
        return redirect(url_for('index'))
    user = session.get('user', None)
    if user is not None:
        if request.method == "POST":
            # Check that it is in fact the leader that nominated
            current_turn = db_session.query(Turns).join(Missions).join(Games).filter(Games.id == game) \
                .order_by(Turns.id.desc()).limit(1).scalar()
            user_player = db_session.query(Players.id).filter(Players.game_id == game, Players.user_id==user).scalar()
            if user_player == current_turn.leader:
                # Gather our nominees
                nominees = []
                nominee_candidates = request.form.values()
                for value in set(nominee_candidates):
                    # Check that the given player_id is part of the game and that the
                    # form value is an integer
                    if value.isdigit() and db_session.query(Players) \
                            .filter(Players.game_id==game, Players.id==value).count() > 0:
                        nominees.append(Nominees(turn_id=current_turn.id,
                            player_id=value))

                players_required = db_session.query(Missions.people_required).join(Turns) \
                        .filter(Turns.id == current_turn.id).scalar()
                # The correct amount of players has been nominated
                if len(nominees) == players_required:
                    db_session().bulk_save_objects(nominees)
                    db_session().commit()


    return redirect(url_for('game', game=game))


@app.route("/<game>/submit-post", methods=["GET", "POST"])
def submit_post(game=None):
    if check_game(game):
        return redirect(url_for('index'))
    if request.method == "GET":
        return redirect(url_for('game', game=game))
    else:
        body = request.form["body"]
        author = session.get('user', None)
        # If there is no author or body is None or empty then just redirect back
        if author is None or not body:
            return redirect(url_for('game', game=game))

        mission_number = db_session.query(Missions).filter(Missions.game_id == game).count()
        post = Posts(author = author,
                game_id = game,
                mission_number = mission_number,
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
