from uuid import uuid4

class Player:
  def __init__(self, name):
    self.name = name
    self.token = uuid4()
    self.score = 0

  def __str__(self):
    return self.name + " " + str(self.token)

  def __repr__(self):
    return str(self)

