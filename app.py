from flask import Flask, render_template, request, redirect
import os
import random
from player import Player
from question import Question

app = Flask(__name__, static_url_path='/static')

players = []
imgs = []
choices = 5
Timer = choices*12


@app.route('/')
def hello():
    global question
    global imgs
    imgs = os.listdir('static')
    imgs = [img[:-4] for img in imgs]

    question = Question(imgs, players, choices)
    print(question)
    return render_template('index.html', players = players_to_table())

@app.route('/game', methods=['POST', 'GET'])
def session():
    scores = []
    for p in players:
        scores.append([p.name, p.score])
    #return '<b>Hello, World!</b><img src="/static/' + question.image + '.png"/>' + str(question.choix) + str(scores)
    return render_template('game.html', players=players_to_table(), img=question.image)

@app.route('/addplayer', methods=['POST'])
def addplayer():
    players.append(Player(str(request.form.get('player_name'))))
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
    print('question ',  question)

    return render_template('player.html', name=player.name,
                           score=player.score, choix=question.players_choices[token],
                           img=question.image, qscore = question.getQuestionValue(token))

@app.route('/choose/<token>/<answer>', methods=['POST', 'GET'])
def choose(token, answer):
    global question
    player = next((x for x in players if x.name == token), None)
    player.score += question.check_answer(player.name, answer)
    if not question.active:
        print('new question')
        #question = Question(imgs, players, choices)
        newQuestion()
    return redirect('/player/' + token)

def players_to_table():
    tbl = []
    players.sort(key=lambda x: x.score, reverse=True)
    for p in players:
        tbl.append([p.name, p.score, p.token])
    return tbl

def newQuestion():
    global question
    question = Question(imgs, players, choices)
    imgs.remove(question.image)

if __name__ == '__main__':
    app.run()