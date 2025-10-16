from uuid import uuid4
import qrcode
import qrcode.image.svg
import random
import os

class Player:
  def __init__(self, name):
    self.name = name
    self.token = uuid4()
    self.score = 0
    
    # Assigner un avatar aléatoire
    avatar_folder = 'static/avatars'
    self.avatar = None  # Initialiser à None par défaut
    
    try:
      if os.path.exists(avatar_folder):
        avatars = [f for f in os.listdir(avatar_folder) if f.endswith('.png')]
        if avatars:
          self.avatar = random.choice(avatars)
          print(f"Assigned avatar {self.avatar} to {name}")
        else:
          print(f"No PNG avatars found in {avatar_folder}")
      else:
        print(f"Warning: Avatar folder '{avatar_folder}' does not exist")
    except Exception as e:
      print(f"Error loading avatar: {e}")
    
    # Si aucun avatar n'a été trouvé, utiliser le premier avatar disponible ou None
    if self.avatar is None:
      try:
        if os.path.exists(avatar_folder):
          all_files = os.listdir(avatar_folder)
          if all_files:
            self.avatar = all_files[0]  # Prendre le premier fichier disponible
            print(f"Using first available file as avatar: {self.avatar}")
          else:
            self.avatar = 'user.png'  # Avatar fictif
            print(f"No files in avatar folder, using default: {self.avatar}")
        else:
          self.avatar = 'user.png'  # Avatar fictif
          print(f"Avatar folder does not exist, using default: {self.avatar}")
      except Exception as e:
        self.avatar = 'user.png'  # Avatar fictif en cas d'erreur
        print(f"Error accessing avatar folder: {e}")
    
    # Créer le dossier players s'il n'existe pas
    players_folder = 'static/players'
    try:
      os.makedirs(players_folder, exist_ok=True)
    except Exception as e:
      print(f"Error creating players folder: {e}")
    
    # Créer le QR code
    try:
      img = qrcode.make('https://five-cats-game.onrender.com/player/' + self.name, image_factory=qrcode.image.svg.SvgImage)
      qr_path = os.path.join(players_folder, self.name + '.svg')
      with open(qr_path, 'wb') as qr:
        img.save(qr)
      print(f"QR code created for {name}")
    except Exception as e:
      print(f"Error creating QR code for {self.name}: {e}")

  def __str__(self):
    return self.name + " " + str(self.token)

  def __repr__(self):
    return str(self)

