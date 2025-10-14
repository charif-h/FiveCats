from flask import Flask, render_template, request, redirect, jsonify
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
game_state = 'waiting'


@app.route('/')
def hello():
    global question
    global imgs
    global game_state
    imgs = os.listdir('static/movies')
    imgs = [img[:-4] for img in imgs]

    #question = Question(imgs, players, choices)
    #print(question)
    return render_template('index.html', players = players_to_table(), game_state = game_state)

@app.route('/game', methods=['POST', 'GET'])
def session():
    global question
    global choices
    global Timer
    global total
    global game_state
    choices = int(request.form['choices'])
    Timer = int(request.form['Timer'])
    total = int(request.form['total'])

    if total == 0:
        total = len(imgs)

    scores = []
    for p in players:
        scores.append([p.name, p.score])

    newQuestion()
    return render_template('game.html', players=players_to_table(), img=question.image, game_state=game_state)

@app.route('/addplayer', methods=['POST'])
def addplayer():
    global game_state
    name = request.form.get('player_name', '').strip()
    error = None
    if not name:
        error = "Le nom du joueur ne peut pas être vide."
    elif any(p.name == name for p in players):
        error = f"Le joueur '{name}' existe déjà."
    if error:
        return render_template('index.html', players=players_to_table(), error=error, game_state=game_state)
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
    global game_state
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
                           img=pq_image, qscore = pq_value, game_state=game_state)

@app.route('/choose/<token>/<answer>', methods=['POST', 'GET'])
def choose(token, answer):
    global question
    player = next((x for x in players if x.name == token), None)
    points_earned = question.check_answer(player.name, answer)
    player.score += points_earned
    
    # Déterminer si la réponse est correcte et envoyer une notification via Socket.IO
    is_correct = points_earned > 0
    if is_correct:
        message = f"<i class='fa-solid fa-check-circle'></i> Bravo ! Réponse correcte ! +{points_earned} points"
        message_type = "success"
    else:
        message = "<i class='fa-solid fa-times-circle'></i> Mauvaise réponse ! Essayez encore."
        message_type = "error"
    
    # Envoyer la notification à tous les clients, mais avec le nom du joueur pour filtrage côté client
    socketio.emit('answer_feedback', {
        'player': token,
        'message': message,
        'type': message_type,
        'is_correct': is_correct,
        'points': points_earned
    })
    
    socketio.emit('update_score', players_to_table(False))
    
    new_question_generated = False
    if not question.active:
        print('new question')
        newQuestion()
        new_question_generated = True
    
    # Si c'est une requête AJAX, retourner JSON au lieu de rediriger
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'fetch' in request.headers.get('User-Agent', '').lower():
        return jsonify({'status': 'success', 'new_question': new_question_generated})
    
    return redirect('/player/' + token)

# Handler for a message recieved over 'connect' channel
@socketio.on('connect')
def handle_connect():
    global game_state
    print('Client connected')
    # Envoyer l'état actuel du jeu au nouveau client
    socketio.emit('game_state_changed', {'state': game_state})

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

@socketio.on('change_game_state')
def handle_change_game_state(data):
    global game_state
    global question
    new_state = data.get('state', 'waiting')
    old_state = game_state
    game_state = new_state
    print(f'Game state changed from {old_state} to: {game_state}')
    
    # Générer une nouvelle question quand on passe à in_progress depuis loading
    if old_state == 'loading' and new_state == 'in_progress':
        if len(imgs) > 0 and len(players) > 0:
            newQuestion()
    
    # Émettre le changement d'état à tous les clients connectés
    socketio.emit('game_state_changed', {'state': game_state})

@socketio.on('countdown_update')
def handle_countdown_update(data):
    count = data.get('count', 0)
    # Diffuser la mise à jour du compte à rebours à tous les clients
    socketio.emit('countdown_update', {'count': count})

@socketio.on('game_paused')
def handle_game_paused():
    print('Game paused - notifying all players')
    socketio.emit('game_paused')

@socketio.on('game_resumed')
def handle_game_resumed():
    print('Game resumed - notifying all players')
    socketio.emit('game_resumed')


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