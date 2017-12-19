# The Resistance

The Resistance is a game that I sometimes play with my friends.

We just started a round online (in skype mainly) and I figured it shouldn't be too hard
to create my own The Resistance game online, even though I have absolutetly zero experience
with web design and front-end. I was wrong. But now I am stuck.

## Build & Run
```Bash
pip install --user flask
```

```Bash
FLASK_ENV_FILE=.env python main.py
```

```
#.env
DEBUG = True
SECRET_KEY = "Not gonna happen"
```

## TODO

- [x] Create a game.html template for better readibility
- [x] Can probably template everything more (This wasn't really true)
- [x] Add support for mission\_votes
- [ ] Style login and signup
- [ ] Create a cronjob that handles the "night cycles"
