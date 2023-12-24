from uuid import uuid4
import qrcode
import qrcode.image.svg

class Player:
  def __init__(self, name):
    self.name = name
    self.token = uuid4()
    self.score = 0
    img = qrcode.make('https://five-cats-game.onrender.com/player/' + self.name, image_factory=qrcode.image.svg.SvgImage)

    with open('static/players/' + self.name + '.svg', 'wb') as qr:
      img.save(qr)

  def __str__(self):
    return self.name + " " + str(self.token)

  def __repr__(self):
    return str(self)

