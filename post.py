import datetime

class Post:
    def __init__(self, user, body):
        self.created = datetime.datetime.now().strftime("%y-%m-%d %H:%M")
        self.user = user
        self.body = body
