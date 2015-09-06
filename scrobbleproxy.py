from flask import Flask, request
app = Flask(__name__)

from yattag import Doc
import yattag

import time
import re
from collections import defaultdict

from mockdata import User, Session, Token

staticuser = "jonty"

@app.route('/api/auth/', methods=['GET'])
def api_auth():
    token = request.args['token']
    return """
        <h4>Approve this client for account '%s'?</h4>
        <form method='POST'>
            <input type='hidden' name='user' value='%s'/>
            <input type='hidden' name='token' value='%s'/>
            <input type='submit' value='Yes please'/>
        </form>
    """ % (staticuser, staticuser, token)

@app.route('/api/auth/', methods=['POST'])
def api_auth_approve():
    user = request.form['user']
    token = Token.load(request.form['token'])
    token.validate(User.load_by_name(user).id)

    return "Token %s approved for user %s, press continue in client." % (token.token, user)

@app.route('/2.0/', methods=['GET'])
def api_get():
    method = request.args['method'].lower()
    if method == 'user.getinfo':
        return user_info(request, request.args)
    elif method == 'auth.gettoken':
        return getToken(request, request.args)
    elif method == 'auth.getsessioninfo':
        return getSessionInfo(request, request.args)

    print "No handler for GET to %s" % method
    return "Nope"

@app.route('/2.0/', methods=['POST'])
def api_post():
    method = request.form['method'].lower()
    if method == 'track.updatenowplaying':
        return now_playing(request, request.form)
    elif method == 'track.scrobble':
        return scrobble(request, request.form)
    elif method == 'auth.getsession':
        return getSession(request, request.form)
    # THIS SHOULD NOT BE A FUCKING POST ARGAHRAG
    elif method == 'user.getinfo':
        return user_info(request, request.form)

    print "No handler for POST to %s" % method
    return "Nope"

def getToken(request, data):
    token = Token.generate()
    print "ISSUING TOKEN %s" % token.token

    doc, tag, text = Doc().tagtext()
    with tag('lfm', status="ok"):
        with tag('token'):
            text(token.token)

    return '<?xml version="1.0" encoding="utf-8"?>\n' + yattag.indent(doc.getvalue())

def getSession(request, data):
    token = Token.load(data['token'])
    if not token:
        print "Invalid token"
        return "NOPE"

    if not token.user:
        print "Token not validated"
        return "NOPE"

    print "GRANTING SESSION for token %s" % token.token
    token.consume()
    session = Session.create(token.user)

    doc, tag, text = Doc().tagtext()
    with tag('lfm', status="ok"):
        with tag('session'):
            with tag('name'):
                text(session.user.name)
            with tag('key'):
                text(session.id)
            with tag('subscriber'):
                text('0')

    return '<?xml version="1.0" encoding="utf-8"?>\n' + yattag.indent(doc.getvalue())

def getSessionInfo(request, data):
    sk  = data['sk']
    
    session = Session.load(sk)
    if not session:
        print "Invalid session"
        return "NOPE"

    print "SESSION INFO for session %s, user %s" % (session.id, session.user.name)

    doc, tag, text = Doc().tagtext()
    with tag('lfm', status="ok"):
        with tag('application'):
            with tag('session'):
                with tag('name'):
                    text(session.user.name)
                with tag('key'):
                    text(session.id)
                with tag('subscriber'):
                    text('0')
            with tag('country'):
                text('US')

    return '<?xml version="1.0" encoding="utf-8"?>\n' + yattag.indent(doc.getvalue())

def scrobble(request, data):
    sk = data['sk']
    session = Session.load(sk)
    if not session:
        print "Invalid session"
        return "NOPE"

    # FUUUUUUU PHP ARRAYS
    lookup = defaultdict(dict)
    for key, value in data.items():
        matches = re.match('(.*)\[(\d+)\]', key)
        if matches:
            key = matches.group(1)
            number = matches.group(2)
        else:
            number = 0
        lookup[number][key] = value

    doc, tag, text = Doc().tagtext()
    with tag('lfm', status="ok"):
        with tag('scrobbles'):

            for _, dataset in lookup.items():
                if 'track' not in dataset:
                    continue

                artist      = dataset['artist']
                track       = dataset['track']
                album       = dataset['album']
                albumArtist = dataset['albumArtist']
                timestamp   = dataset['timestamp']

                print "SCROBBLE- User: %s, Artist: %s, Track: %s, Album: %s"  \
                    % (session.user.name, artist, track, album)

                session.user.scrobble(timestamp, artist, track, album, albumArtist)

                with tag('scrobble'):
                    with tag('track', corrected="0"):
                        text(track)
                    with tag('artist', corrected="0"):
                        text(artist)
                    with tag('album', corrected="0"):
                        text(album)
                    with tag('albumArtist', corrected="0"):
                        text(albumArtist)
                    with tag('timestamp', corrected="0"):
                        text(timestamp)
                    with tag('ignoredMessage', code="0"):
                        text('')

    return '<?xml version="1.0" encoding="utf-8"?>\n' + yattag.indent(doc.getvalue())

def now_playing(request, data):
    sk = data['sk']
    session = Session.load(sk)
    if not session:
        print "Invalid session"
        return "NOPE"

    track   = data['track']
    artist  = data['artist']
    album   = data['album']
    albumArtist   = data['albumArtist']
    
    print "NOW PLAYING- User: %s, Artist: %s, Track: %s, Album: %s"  \
        % (session.user.name, artist, track, album)

    doc, tag, text = Doc().tagtext()
    with tag('lfm', status="ok"):
        with tag('nowplaying'):
            with tag('track', corrected="0"):
                text(track)
            with tag('artist', corrected="0"):
                text(artist)
            with tag('album', corrected="0"):
                text(album)
            with tag('albumArtist', corrected="0"):
                text(albumArtist)
            with tag('ignoredMessage', code="0"):
                text('')

    return '<?xml version="1.0" encoding="utf-8"?>\n' + yattag.indent(doc.getvalue())

def user_info(request, data):
    sk = data['sk']
    session = Session.load(sk)
    if not session:
        print "Invalid session"
        return "NOPE"

    doc, tag, text = Doc().tagtext()
    with tag('lfm', status="ok"):
        with tag('user'):
            with tag('name'):
                text(session.user.name)
            with tag('realname'):
                text(session.user.name)
            with tag('url'):
                text('http://foo.bar/user/' + session.user.name)
            with tag('playcount'):
                text('9001')
            with tag('registered', unixtime=str(time)):
                text(session.user.timestamp)

    return '<?xml version="1.0" encoding="utf-8"?>\n' + yattag.indent(doc.getvalue())


if __name__ == '__main__':
    app.config.update(
        DEBUG=True
    )
    app.run(port=80)
