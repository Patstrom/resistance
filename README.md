# The Resistance

The Resistance is a game that I sometimes play with my friends.

We just started a round online (in skype mainly) and I figured it shouldn't be too hard
to create my own The Resistance game online, even though I have absolutetly zero experience
with web design and front-end. I was wrong. But now I am stuck.

## Build & Run
Install requirements from requirements.txt

```Bash
pip install -r requirements.txt
```

There are 3 environment variables

| Environment Variable | Comment                                                |
|----------------------|--------------------------------------------------------|
| DEBUG                | 'True' if debug output is wanted, otherwise any string |
| SECRET\_KEY          | The secret key used for sessions management            |
| DATABASE\_URL        | The 'postgres://user@host/database' url                |


```Bash
gunicorn app:app
```


## TODO

- [x] Create a game.html template for better readibility
- [x] Can probably template everything more (This wasn't really true)
- [x] Add support for mission\_votes
- [x] Style login and signup
- [x] Create a cronjob that handles the "night cycles"
- [ ] Make advancer post a summary of changes to game (by a name that you blacklist for signup)
- [ ] Add some buttons to filter posts by missions
- [ ] Add a rules page that explains avalon as well as default behavior for this app (midnight cycles, random nominees, votes etc)
