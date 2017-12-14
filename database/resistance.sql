CREATE TABLE users(
    id      serial primary key,
    name    text not null unique,
    pwhash  text not null
);

CREATE TABLE games(
    id      serial primary key,
    name    text not null,
    creator integer references Users,
    started boolean not null default false,
    is_over boolean not null default false
);

CREATE TABLE players(
    id      serial primary key,
    game_id integer not null references Games,
    user_id integer not null references Users,
    is_spy  boolean default false
);

CREATE TABLE missions(
    id              serial primary key,
    game_id         integer not null references Games,
    fails_required  smallint check(fails_required between 1 and 2),
    people_required smallint check(people_required between 2 and 5),
    success boolean default false
);

CREATE TABLE turns(
    id          serial primary key,
    mission_id  integer not null references Missions,
    leader      integer not null references Players,
    approved    boolean default false
);

CREATE TABLE nominees(
    turn_id     integer references Turns,
    player_id   integer references Players,
    primary key (turn_id, player_id)
);

CREATE TABLE turn_votes (
    turn_id     integer references Turns,
    player_id   integer references Players,
    approve     boolean not null,
    primary key (turn_id, player_id)
);

CREATE TABLE mission_votes(
    mission_id  integer references Missions
    player_id   integer references Players,
    fail        boolean default false,
    primary key (mission_id, player_id)
)

CREATE TABLE posts(
    id          serial primary key,
    author      integer not null references Users,
    game_id     integer not null references Games,
    mission_id  integer references Missions,
    body        text not null,
    created_at  timestamp default current_timestamp
);
