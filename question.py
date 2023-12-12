import random

class Question:
    def __init__(self, imgs, players):
        self.choix = random.sample(imgs, k=10)
        self.image = random.choice(self.choix)
        self.choix.sort()
        self.active = True
        self.score_id = 9
        self.scores = [0, 1, 2, 3, 5, 8, 13, 21, 34, 55]
        self.players_choices = {}
        for p in players:
            self.players_choices[p.name] = self.choix.copy()

    def __str__(self):
        return self.image + str(self.choix)

    def check_answer(self, player_token, answer):
        ret = 0
        if (answer == self.image):
            ret = self.getQuestionValue(player_token)
            self.players_choices[player_token] = []
            self.active = sum(len(pc) > 0 for pc in self.players_choices.values()) > 0
            print(sum(len(pc) > 0 for pc in self.players_choices.values()), self.active)
            self.score_id -= 1
        else:
            self.players_choices[player_token].remove(answer)

        return ret

    def getQuestionValue(self, player_token=None):
        if player_token is None:
            return self.scores[self.score_id]
        else:
            return min(self.scores[len(self.players_choices[player_token]) - 1], self.scores[self.score_id])
