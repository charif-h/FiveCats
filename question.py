import random

class Question:
    def __init__(self, imgs, players, choices):
        self.choix = random.sample(imgs, k=choices)
        self.image = random.choice(self.choix)
        self.choix.sort()
        self.active = True
        self.score_id = choices - 1
        self.scores = [0, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377, 610]
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
            # Check if question is still active: only count active players
            active_players_with_choices = sum(
                1 for player_name, choices in self.players_choices.items()
                if len(choices) > 0 and self._is_player_active(player_name)
            )
            self.active = active_players_with_choices > 0
            print(f"Active players with choices: {active_players_with_choices}, Question active: {self.active}")
            self.score_id -= 1
        else:
            self.players_choices[player_token].remove(answer)

        return ret
    
    def _is_player_active(self, player_name):
        """Check if a player is active (helper method for checking player status)"""
        # This will be set from app.py when the question is created
        if hasattr(self, 'players_status'):
            return self.players_status.get(player_name, False)
        return True  # Default to True if status not set

    def time_out(self):
        for p in self.players_choices.keys():
            self.players_choices[p] = []
        # Mettre à jour le statut actif après le timeout
        self.active = False

    def getQuestionValue(self, player_token=None):
        if player_token is None:
            return self.scores[self.score_id]
        else:
            return min(self.scores[len(self.players_choices[player_token]) - 1], self.scores[self.score_id])

    def choices_to_json(self):
        print("ici ...")
        print(self.players_choices)
        print()
        # Retourner directement le dictionnaire au lieu d'utiliser jsonify
        return self.players_choices

