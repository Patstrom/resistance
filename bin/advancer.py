"""
This script updates the game state of all ongoing games

It does this by checking the current mission for each ongoing game.

If the team is chosen for the mission, it checks if the missions has succeded. If the game
is over it sets the appropriate flags. Otherwise it adds another mission.

If the team is not chosen it checks the current turn to determine if the nominees have been
approved. If they have it sets the appropriate flags. If the nominees aren't approved it
creates a new turn with a new leader.
"""

from resistance_rules import *

from database import load_session
db_session = load_session()
from models import *

def advance_games():
    # Get all ongoing games
    games = db_session.query(Games).filter(Games.started == True, Games.is_over == False).all()

    # Iterate over games
    for game in games:
        print("Processing game: {}".format(game.id))
        # Get current missions
        current_mission = db_session.query(Missions).filter(Missions.game_id == game.id) \
                .order_by(Missions.id.desc()).limit(1).scalar()
        print("Current_mission: {}".format(current_mission.id))

        if current_mission.team_is_chosen: # Check if missions succeeds and if game should continue
            # Get how many missions there are
            number_of_missions = db_session.query(Missions).filter(Missions.game_id==game.id).count()
            number_of_successful_missions = db_session.query(Missions).filter(Missions.game_id==game.id,
                Missions.success==True).count()
            number_of_failed_missions = number_of_missions - number_of_successful_missions
     
            # Get votes
            mission_votes = db_session.query(MissionVotes).filter(MissionVotes.mission_id==current_mission.id).all()

            # Unzip result
            mission_votes = [vote.fail for vote in mission_votes]

            # Get the number of players
            number_of_players = db_session.query(Players).filter(Players.game_id==game.id).count()

            if mission_votes.count(True) >= current_mission.fails_required:
                current_mission.success = False
                number_of_failed_missions += 1
            else:
                current_mission.success = True
                number_of_successful_missions += 1
            db_session().merge(current_mission)

            # Check win condition
            number_of_players = 5
            missions_required = len(number_of_players_for_mission[number_of_players]) / 2 + 1
            if (number_of_successful_missions >= missions_required
                or number_of_failed_missions >= missions_required):
                print("Game: {} is over".format(game.id))
                game.is_over = True
                db_session().merge(game)
                continue # This game is done, continue with next one
            
            # Add next mission
            print("Adding new mission for game: {}".format(game.id))
            # If we are adding the fourth mission for 7 or more players it should require two people
            fails_required = 2 if number_of_missions==3 and number_of_players>=7 else 1
            next_mission = Missions(game_id=game.id,
                    fails_required=fails_required,
                    # Since the number_of_players_for_mission list is 0 indexed we use
                    # number_of_missions as index for how many we need for the next mission.
                    # (people required for mission 4 is located at index 3, the number of missions
                    # we currently have)
                    people_required=number_of_players_for_mission[number_of_players][number_of_missions])

            db_session.add(next_mission)
            db_session.flush()
            current_leader = db_session.query(Turns.leader).filter(Turns.mission_id==current_mission.id) \
                    .order_by(Turns.id.desc()).limit(1).scalar()
            next_leader = db_session.query(LeaderOrder.next_leader) \
                    .filter(LeaderOrder.game_id==game.id, LeaderOrder.current_leader==current_leader).scalar()
            db_session.add(Turns(mission_id=next_mission.id, leader=next_leader))
        else: # we are still trying to nominate a team.
        # Get turns
            turns = db_session.query(Turns).filter(Missions.id == current_mission.id) \
                .order_by(Turns.id.desc()).all()

            current_turn = turns[-1]
            print("current turn: {}".format(current_turn.id))

            # Get all votes and see if it passes
            turn_votes = db_session.query(TurnVotes.approve).filter(TurnVotes.turn_id == current_turn.id) \
                    .all()

            # Unzip the votes
            turn_votes = [vote.approve for vote in turn_votes]

            # Find out how many approves we have
            approves = turn_votes.count(True)
            fails = turn_votes.count(False)

            # The nominees are approved (or the votes don't matter).
            # ties are fails.
            if approves > fails or len(turns) == 5:
                current_turn.approved = True
                current_mission.team_is_chosen = True
                print("Updating database to reflect that team is chosen")
                db_session().merge(current_turn)
                db_session().merge(current_mission)
            else: # Advance the game
                print("Team wasn't chosen; inserting new turn")
                next_leader = db_session.query(LeaderOrder.next_leader) \
                        .filter(LeaderOrder.game_id==game.id, LeaderOrder.current_leader==current_turn.leader).scalar()
                db_session.add(Turns(mission_id=current_mission.id, leader=next_leader))

        print("Committing database changes")
        db_session().commit() # commit the changes


if __name__ == "__main__":
    advance_games()
