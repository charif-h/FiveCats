from flask import Flask, render_template, request, redirect, jsonify
from flask_socketio import SocketIO
import os
import time
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
previous_state = None  # Pour mémoriser l'état avant pause

def set_game_state(new_state, broadcast=True):
    """Fonction centralisée pour changer le game_state et assurer la synchronisation"""
    global game_state, previous_state
    old_state = game_state
    
    # Si on passe en pause, mémoriser l'état précédent
    if new_state == 'paused' and old_state != 'paused':
        previous_state = old_state
    
    game_state = new_state
    print(f'Game state changed from {old_state} to: {game_state}')
    
    if broadcast:
        # Toujours diffuser le changement d'état à tous les clients connectés
        socketio.emit('game_state_changed', {
            'state': game_state, 
            'timestamp': time.time(),
            'previous_state': previous_state
        })
    
    return old_state


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
    set_game_state('loading')  # Utiliser la fonction centralisée
    choices = int(request.form['choices'])
    Timer = int(request.form['Timer'])
    total = int(request.form['total'])

    if total == 0:
        total = len(imgs)

    scores = []
    for p in players:
        scores.append([p.name, p.score])

    # Ne pas créer la question tout de suite, attendre la fin du countdown
    return render_template('game.html', players=players_to_table(), img="", game_state=game_state)

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

@app.route('/terminate_game', methods=['POST'])
def terminate_game():
    global question
    if game_state in ['loading', 'in_progress', 'paused']:
        # Terminer le jeu en cours
        socketio.emit('end_game', {
            'reason': 'manual',
            'final_scores': players_to_table(False),
            'winner': get_winner() if players else None,
            'message': 'Le jeu a été terminé manuellement par l\'administrateur.'
        })
        set_game_state('waiting')  # Utiliser la fonction centralisée
        # Nettoyer la question active
        if 'question' in globals():
            del question
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
    pq_value = 0  # Valeur par défaut
    if 'question' in globals() and question is not None:
        pq_choix = question.players_choices[token]
        pq_image = question.image
        pq_value = question.getQuestionValue(token)
        print(f"Question exists - {token} score: {pq_value}")
    else:
        print(f"No active question - {token} score: {pq_value}")

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
        
        # Si bonne réponse, masquer toutes les autres options pour ce joueur
        socketio.emit('hide_other_choices', {
            'player': token,
            'correct_answer': question.image
        })
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
    
    # Calculer et envoyer les nouveaux scores pour tous les joueurs après chaque réponse
    updated_total_scores = {}
    updated_question_scores = {}
    for p in players:
        updated_total_scores[p.name] = p.score  # Score total cumulé du joueur
        updated_question_scores[p.name] = question.getQuestionValue(p.name)  # Score de la question actuelle
    
    socketio.emit('score_update', {
        'player_scores': updated_total_scores,
        'question_scores': updated_question_scores,
        'global_score_id': question.score_id
    })
    
    socketio.emit('update_score', players_to_table(False))
    
    # Vérifier si la question est terminée (tous ont trouvé OU plus d'options)
    new_question_generated = False
    if not question.active:
        print('Question finished - entering recharging state')
        set_game_state('recharging')
        
        # Afficher la réponse correcte et démarrer le countdown de 5 secondes
        socketio.emit('show_correct_answer', {
            'correct_answer': question.image,
            'message': f'La bonne réponse était : {question.image}'
        })
        
        # Démarrer le délai de recharge
        socketio.start_background_task(recharging_countdown)
        new_question_generated = True
    
    # Si c'est une requête AJAX, retourner JSON au lieu de rediriger
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'fetch' in request.headers.get('User-Agent', '').lower():
        return jsonify({'status': 'success', 'new_question': new_question_generated})
    
    return redirect('/player/' + token)

# Handler for a message recieved over 'connect' channel
@socketio.on('connect')
def handle_connect():
    print('Client connected')
    # Envoyer l'état actuel du jeu au nouveau client avec timestamp
    socketio.emit('game_state_changed', {
        'state': game_state, 
        'timestamp': time.time(),
        'sync': True  # Indique que c'est une synchronisation initiale
    })

@socketio.on('ping_game_state')
def handle_ping_game_state():
    """Gestionnaire pour les demandes de synchronisation du game_state"""
    socketio.emit('game_state_sync', {
        'state': game_state,
        'timestamp': time.time()
    })

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
    socketio.emit('update_score', players_to_table(False))
    
    # Vérifier si la question est devenue inactive après le timeout
    if not question.active:
        print('Question expired - entering recharging state')
        set_game_state('recharging')
        
        # Afficher la réponse correcte
        socketio.emit('show_correct_answer', {
            'correct_answer': question.image,
            'message': f'Temps écoulé ! La bonne réponse était : {question.image}'
        })
        
        # Démarrer le countdown de recharge
        socketio.start_background_task(recharging_countdown)

def delayed_new_question():
    import time
    with app.app_context():  # Créer un contexte d'application Flask
        time.sleep(5)  # Attendre 5 secondes
        print('Generating new question after EXPIRED delay')
        newQuestion()

def recharging_countdown():
    """Gère le countdown de 5 secondes en état recharging"""
    import time
    with app.app_context():
        # Envoyer le countdown de recharge
        for i in range(5, 0, -1):
            socketio.emit('recharging_countdown', {'count': i})
            time.sleep(1)
        
        # Après le countdown, retourner à in_progress avec nouvelle question
        print('Recharging finished - returning to in_progress')
        set_game_state('in_progress')
        newQuestion()

def delayed_disconnect_all():
    """Déconnecte tous les clients après la fin du jeu"""
    import time
    with app.app_context():
        time.sleep(10)  # Attendre 10 secondes pour que les clients voient l'écran de fin
        print('Disconnecting all clients after game end')
        socketio.emit('force_disconnect')

@socketio.on('change_game_state')
def handle_change_game_state(data):
    global question, previous_state
    new_state = data.get('state', 'waiting')
    old_state = set_game_state(new_state)  # Utiliser la fonction centralisée
    
    # Générer une nouvelle question quand on passe à in_progress depuis loading
    if old_state == 'loading' and new_state == 'in_progress':
        if len(imgs) > 0 and len(players) > 0:
            newQuestion()
    
    # Restaurer l'état précédent si on sort de pause
    elif old_state == 'paused' and new_state == 'continue':
        if previous_state:
            set_game_state(previous_state)
            previous_state = None

@socketio.on('countdown_update')
def handle_countdown_update(data):
    count = data.get('count', 0)
    # Diffuser la mise à jour du compte à rebours à tous les clients
    socketio.emit('countdown_update', {'count': count})

@socketio.on('game_paused')
def handle_game_paused():
    print('Game paused - notifying all players')
    set_game_state('paused')

@socketio.on('game_resumed')
def handle_game_resumed():
    global previous_state
    print('Game resumed - notifying all players')
    if previous_state:
        set_game_state(previous_state)
        previous_state = None
    else:
        set_game_state('in_progress')  # Fallback

@socketio.on('end_game')
def handle_end_game(data=None):
    reason = data.get('reason', 'manual') if data else 'manual'
    set_game_state('finished')
    
    final_scores = players_to_table(False)
    winner = get_winner() if players else None
    
    print(f'Game ended - Reason: {reason}')
    socketio.emit('game_finished', {
        'reason': reason,
        'final_scores': final_scores,
        'winner': winner,
        'message': get_end_game_message(reason, winner)
    })
    
    # Déconnecter tous les clients après 10 secondes
    socketio.start_background_task(delayed_disconnect_all)

def get_winner():
    if not players:
        return None
    sorted_players = sorted(players, key=lambda x: x.score, reverse=True)
    return {
        'name': sorted_players[0].name,
        'score': sorted_players[0].score
    }

def get_end_game_message(reason, winner):
    messages = {
        'manual': 'Le jeu a été terminé manuellement.',
        'no_more_images': 'Toutes les images ont été utilisées !',
        'time_limit': 'Le temps limite du jeu a été atteint.',
        'target_reached': f'{winner["name"] if winner else "Un joueur"} a atteint le score cible !'
    }
    return messages.get(reason, 'Le jeu est terminé.')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')
    # Optionnel: retirer le joueur de la liste si nécessaire

@socketio.on('reset_game')
def handle_reset_game():
    global players, imgs, question
    set_game_state('waiting')
    
    # Réinitialiser les scores des joueurs
    for player in players:
        player.score = 0
    
    # Recharger les images
    imgs = os.listdir('static/movies')
    imgs = [img[:-4] for img in imgs]
    
    # Réinitialiser la question
    if 'question' in globals():
        del question
    
    print('Game reset')
    socketio.emit('game_reset')


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
    global question, game_state
    
    # Vérifier s'il reste des images
    if len(imgs) == 0:
        print('No more images available - ending game')
        socketio.emit('end_game', {'reason': 'no_more_images'})
        return
    
    question = Question(imgs, players, choices)
    imgs.remove(question.image)
    print(question.choices_to_json())
    
    # Calculer les scores pour chaque joueur
    player_total_scores = {}
    player_question_scores = {}
    for player in players:
        player_total_scores[player.name] = player.score  # Score total cumulé du joueur
        player_question_scores[player.name] = question.getQuestionValue(player.name)  # Score de la question actuelle
    
    socketio.emit('new_question', {
        'image': question.image, 
        'choices': question.choix,
        'player_scores': player_total_scores,
        'question_scores': player_question_scores
    })


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', allow_unsafe_werkzeug=True)