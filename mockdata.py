import os
import binascii
import sqlite3

class User(object):
    @staticmethod
    def load_by_name(name):
        with sqlite3.connect('database.db') as conn:
            c = conn.cursor()
            c.execute('SELECT * FROM users WHERE name=?', (name,))
            row = c.fetchone()
            if row:
                return User(row)
            return None

    @staticmethod
    def load_by_id(id):
        with sqlite3.connect('database.db') as conn:
            c = conn.cursor()
            c.execute('SELECT * FROM users WHERE id=?', (id,))
            row = c.fetchone()
            if row:
                return User(row)
            return None

    def __init__(self, row):
        id, name, timestamp = row
        self.id = id
        self.name = name
        self.timestamp = timestamp

    def scrobble(self, timestamp, artist, track, album, albumArtist):
        with sqlite3.connect('database.db') as conn:
            c = conn.cursor()
            c.execute('INSERT INTO scrobbles (user, timestamp, artist, track, album, albumArtist) values (?,?,?,?,?,?);', (self.id, timestamp, artist, track, album, albumArtist,))
        

class Session(object):
    @staticmethod
    def load(session):
        with sqlite3.connect('database.db') as conn:
            c = conn.cursor()
            c.execute('SELECT * FROM sessions WHERE id=?', (session,))
            row = c.fetchone()
            if row:
                return Session(row)
            return None

    @staticmethod
    def create(user):
        session = binascii.b2a_hex(os.urandom(20))
        with sqlite3.connect('database.db') as conn:
            c = conn.cursor()
            c.execute('INSERT INTO sessions (id, user) VALUES (?,?);', (session, user.id,))
        return Session.load(session)

    def __init__(self, row):
        id, user, timestamp = row
        self.id = id
        self.user = User.load_by_id(user)
        self.timestamp = timestamp


class Token(object):
    @staticmethod
    def load(token):
        with sqlite3.connect('database.db') as conn:
            c = conn.cursor()
            c.execute('SELECT * FROM tokens WHERE token=?', (token,))
            row = c.fetchone()
            if row:
                return Token(row)
            return None

    @staticmethod
    def generate():
        token = binascii.b2a_hex(os.urandom(20))
        with sqlite3.connect('database.db') as conn:
            c = conn.cursor()
            c.execute('INSERT INTO tokens (token) VALUES (?);', (token,))
        return Token.load(token)

    def __init__(self, row):
        token, user, timestamp = row
        self.token = token
        self.timestamp = timestamp
        self.user = None
        if user:
            self.user = User.load_by_id(user)

    def validate(self, user):
        with sqlite3.connect('database.db') as conn:
            c = conn.cursor()
            c.execute('UPDATE tokens SET user = ? WHERE token=?', (user, self.token,))

    def consume(self):
        with sqlite3.connect('database.db') as conn:
            c = conn.cursor()
            c.execute('DELETE FROM tokens WHERE token=?', (self.token,))
