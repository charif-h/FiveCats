from flask import Flask, render_template, request, redirect
from flask_socketio import SocketIO
import os
from player import Player
from question import Question

app = Flask(__name__, static_url_path='/static')
socketio = SocketIO(app)

players = []
imgs = []
choices = 10
Timer = choices*6
total = 0


@app.route('/')
def hello():
    global question
    global imgs
    imgs = os.listdir('static/movies')
    imgs = [img[:-4] for img in imgs]

    #question = Question(imgs, players, choices)
    #print(question)
    return render_template('index.html', players = players_to_table())

@app.route('/game', methods=['POST', 'GET'])
def session():
    global question
    global choices
    global Timer
    global total
    choices = int(request.form['choices'])
    Timer = int(request.form['Timer'])
    total = int(request.form['total'])

    if total == 0:
        total = len(imgs)

    scores = []
    for p in players:
        scores.append([p.name, p.score])

    newQuestion()
    return render_template('game.html', players=players_to_table(), img=question.image)

@app.route('/addplayer', methods=['POST'])
def addplayer():
    name = request.form.get('player_name', '').strip()
    error = None
    if not name:
        error = "Le nom du joueur ne peut pas être vide."
    elif any(p.name == name for p in players):
        error = f"Le joueur '{name}' existe déjà."
    if error:
        return render_template('index.html', players=players_to_table(), error=error)
    players.append(Player(name))
    return redirect('/')

@app.route('/deleteplayer', methods=['POST'])
def deleteplayer():
    name = request.form.get('player_name')
    global players
    players = [p for p in players if p.name != name]
    return redirect('/')

@app.route('/player/<token>', methods=['POST', 'GET'])
def player(token):
    global question
    s = "Hello "
    player = None
    for p in players:
        if str(p.name) == token:
            s += p.name
            player = p

    pq_choix = ""
    pq_image = ""
    pq_value = ""
    if 'question' in globals():
        pq_choix = question.players_choices[token]
        pq_image = question.image
        pq_value = question.getQuestionValue(token)
        print("question exists")


    return render_template('player.html', name=player.name,
                           score=player.score, choix=pq_choix,
                           img=pq_image, qscore = pq_value)

@app.route('/choose/<token>/<answer>', methods=['POST', 'GET'])
def choose(token, answer):
    global question
    player = next((x for x in players if x.name == token), None)
    player.score += question.check_answer(player.name, answer)
    #socketio.emit('update_score', {'name':token, 'score':player.score})
    socketio.emit('update_score', players_to_table(False))
    if not question.active:
        print('new question')
        newQuestion()
    return redirect('/player/' + token)

# Handler for a message recieved over 'connect' channel
@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('start_game')
def handle_start_game():
    # Envoie le signal de démarrage à tous les clients
    socketio.emit('countdown', {'seconds': 3}, broadcast=True)

@socketio.on('message')
def handle_message(message):
    print('Received message:', message)
    socketio.emit('response', 'you said ' + message)

@socketio.on('time_out')
def handle_timeout():
    global question
    question.time_out()
    print(question)
    socketio.emit('time_out')
    socketio.emit('update_score', players_to_table(False))


def players_to_table(with_token = True):
    tbl = []
    players.sort(key=lambda x: x.score, reverse=True)
    for p in players:
        if with_token:
            tbl.append([p.name, p.score, p.token])
        else:
            tbl.append([p.name, p.score])
    return tbl

def newQuestion():
    global question
    question = Question(imgs, players, choices)
    imgs.remove(question.image)
    print(question.choices_to_json())
    socketio.emit('new_question', {'image': question.image, 'choices': question.choix})


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', allow_unsafe_werkzeug=True)