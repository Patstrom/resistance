CREATE TABLE users(
    id      serial primary key,
    name    text not null unique,
    pwhash  text not null
);

CREATE TABLE games(
    id      serial primary key,
    name    text not null unique,
    creator integer not null references Users,
    started boolean not null default false,
    is_over boolean not null default false
);

CREATE TABLE players(
    id      serial primary key,
    game_id integer not null references Games,
    user_id integer not null references Users,
    is_spy  boolean default false,
    unique  (user_id, game_id)
);

CREATE TABLE missions(
    id              serial primary key,
    game_id         integer not null references Games,
    fails_required  smallint not null check(fails_required between 1 and 2),
    people_required smallint not null check(people_required between 2 and 5),
    team_is_chosen  boolean default false,
    success         boolean default false
);

CREATE TABLE turns(
    id          serial primary key,
    mission_id  integer not null references Missions,
    leader      integer not null references Players,
    approved    boolean default false,
    unique(mission_id, leader)
);

CREATE TABLE nominees(
    turn_id     integer not null references Turns,
    player_id   integer not null references Players,
    primary key (turn_id, player_id)
);

CREATE TABLE turn_votes (
    turn_id     integer not null references Turns,
    player_id   integer not null references Players,
    approve     boolean not null,
    primary key (turn_id, player_id)
);

CREATE TABLE mission_votes(
    mission_id  integer not null references Missions,
    player_id   integer not null references Players,
    fail        boolean not null,
    primary key (mission_id, player_id)
);

CREATE TABLE leader_order(
    game_id         integer not null references Games,
    current_leader  integer not null references Players,
    next_leader     integer not null references Players,
    primary key     (game_id, current_leader)
);

CREATE TABLE posts(
    id          serial primary key,
    author      integer not null references Users,
    game_id     integer not null references Games,
    mission_id  integer references Missions,
    body        text not null,
    created_at  timestamp default current_timestamp
);
