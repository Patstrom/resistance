CREATE EXTENSION pgcrypto;

CREATE TABLE Users(
    id          uuid not null default gen_random_uuid() primary key,
    username    text not null,
    pwhash      text not null
)

CREATE TABLE Games(
    id      serial primary key,
    name    test not null,
    started boolean not null default false,
    is_over boolean not null default false
)

CREATE TABLE Players(
    id      serial primary key,
    game_id references Games,
    user_id uuid references Users,
    is_spy  boolean default false
)

CREATE TABLE Missions(
    id              serial primary key,
    game_id         integer references Games,
    fails_required  smallint check(fails_required between 1 and 2),
    people_required smallint check(people_required between 2 and 5)
)


CREATE TABLE Turns(
    id          serial primary key,
    mission_id  references Missions,
    leader      integer references Players,
)

CREATE TABLE Nominees(
    turn_id     integer references Turns,
    player_id   integer references Players,
    UNIQUE(mission_id, player_id)
)

CREATE TABLE Votes (
    turn_id     integer references Turns,
    player_id   references Players,
    approve     boolean not null,
    primary key (turn_id, player_id)
)
