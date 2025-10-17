# 🐱 FiveCats - Movie Guessing Game

FiveCats is an interactive, multiplayer movie guessing game built with Flask and Flask-SocketIO. Players compete in real-time to identify movie posters from a selection of choices, earning points based on their accuracy and speed.

## 🎮 Game Overview

FiveCats is a fun, competitive game where players:
- Scan a QR code to join the game from their mobile devices
- View movie posters and select from multiple choice options
- Earn points using a Fibonacci-based scoring system (the fewer wrong guesses, the more points!)
- Compete in real-time with other players on a shared game board
- Race against the clock to identify movies before time runs out

## ✨ Features

- **Multi-player Support**: Multiple players can join and compete simultaneously
- **QR Code Integration**: Each player gets a unique QR code for easy mobile access
- **Real-time Updates**: Live score updates and game synchronization using WebSockets
- **Dynamic Scoring**: Fibonacci-based scoring system (0, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233 points)
- **Configurable Game Settings**:
  - Adjustable number of choices per question (2-15)
  - Customizable time per question (10-90 seconds)
  - Flexible game ending modes:
    - Limited number of questions (0 = all available questions)
    - Target score (first player to reach the target wins)
- **Responsive Design**: Beautiful, cat-themed UI with Bootstrap styling
- **Movie Database**: Comes with a collection of classic and popular movie posters

## 🚀 Installation

### Prerequisites

- Python 3.7 or higher
- pip (Python package manager)

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/charif-h/FiveCats.git
   cd FiveCats
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Prepare directories**
   
   Ensure the following directories exist:
   - `static/movies/` - Contains movie poster images (PNG format)
   - `static/players/` - Will store generated QR codes for players
   - `static/backgrounds/` - Contains background images

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Access the game**
   
   Open your browser and navigate to:
   ```
   http://localhost:5000
   ```

## 🎯 How to Play

### Setting Up a Game

1. **Add Players**: 
   - On the home page, enter player names and click "Ajouter" (Add)
   - Each player gets a unique QR code displayed in the table

2. **Configure Game Settings**:
   - **Number of choices per question**: Choose between 2-15 options (default: 10)
   - **Time per question**: Set timer from 10-90 seconds (default: 30)
   - **Game ending mode**: Choose between:
     - **Question limit**: Set total number of questions or 0 for all available (default: 0)
     - **Points target**: Set a maximum score to reach (default: 500)

3. **Start the Game**:
   - Click the "Go" button to launch the game board in a new window

### Playing the Game

1. **For the Game Host**:
   - The game board displays the current movie poster
   - A countdown timer shows remaining time
   - Real-time leaderboard displays all players' scores
   - The game automatically advances to the next question

2. **For Players**:
   - Scan your personal QR code or click your name to open your player interface
   - View the current movie poster on your device
   - Select from the available movie title choices
   - See your current score and the question's point value
   - Submit your answer before time runs out!

### Scoring System

- Points are awarded using a Fibonacci sequence based on the number of choices: **0, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233**
- With 2 choices, you can win 1 point
- With 3 choices, you can win 2 points
- With 4 choices, you can win 3 points (1+2)
- With 5 choices, you can win 5 points (2+3)
- With 10 choices (default), you can win 55 points
- With 15 choices (maximum), you can win 610 points
- Your score depends on:
  - How many choices remain (fewer incorrect guesses = more points)
  - The current maximum score available for the question
- First correct answer gets maximum available points
- Wrong answers eliminate that choice but reduce potential points for the question
- No points if time runs out

## 🛠️ Technology Stack

- **Backend**: 
  - Flask 2.3.2 - Web framework
  - Flask-SocketIO 5.3.6 - Real-time bidirectional communication
  
- **Frontend**:
  - HTML5/CSS3
  - JavaScript
  - Bootstrap 5.0.2 - Responsive UI framework
  - Font Awesome 6.4.0 - Icons
  - Socket.IO 3.1.3 - Client-side WebSocket library

- **Additional Libraries**:
  - qrcode 7.4.2 - QR code generation for player access

## 📁 Project Structure

```
FiveCats/
│
├── app.py                  # Main Flask application
├── player.py               # Player class and management
├── question.py             # Question/quiz logic
├── requirements.txt        # Python dependencies
│
├── static/
│   ├── movies/            # Movie poster images (PNG)
│   ├── players/           # Generated QR codes (SVG)
│   ├── backgrounds/       # Background images
│   └── logo-cat.png       # Game logo
│
└── templates/
    ├── index.html         # Home page (player management & settings)
    ├── game.html          # Game board (host view)
    └── player.html        # Player interface (mobile view)
```

## 🎲 Game Mechanics

### Question Class
- Randomly selects a subset of movies for each question
- Tracks each player's remaining choices
- Calculates scores based on Fibonacci sequence
- Manages question state and timeout

### Player Class
- Stores player name and unique token
- Tracks cumulative score
- Generates personal QR code for mobile access

### Real-time Communication
- WebSocket events for:
  - Score updates
  - New question notifications
  - Timeout handling
  - Player connections

## ⚙️ Configuration

The game can be configured through the web interface or by modifying default values in `app.py`:

```python
choices = 10        # Number of choices per question (2-15)
Timer = 30          # Time per question in seconds (10-90)
total = 0           # Total questions (0 = all available, only used in 'questions' mode)
end_mode = 'questions'  # Game ending mode: 'questions' or 'points'
max_points = 500    # Maximum points to reach (only used in 'points' mode)
```

## 🌐 Deployment

The application is designed to run on platforms like Render, Heroku, or any Python-compatible hosting service.

**Important**: Update the QR code URL in `player.py` to match your deployment URL:
```python
img = qrcode.make('https://your-domain.com/player/' + self.name, ...)
```

## 🐛 Troubleshooting

- **QR codes not generating**: Ensure the `static/players/` directory exists and has write permissions
- **Movies not loading**: Verify movie poster images are in `static/movies/` as PNG files
- **WebSocket connection issues**: Check firewall settings and ensure port 5000 is accessible
- **Players can't connect**: Update the QR code URL in `player.py` to your actual domain

## 📝 License

This project is open source and available for educational and entertainment purposes.

## 🤝 Contributing

Contributions are welcome! Feel free to:
- Add more movie posters to the database
- Improve the UI/UX
- Add new features (difficulty levels, categories, etc.)
- Fix bugs or optimize code

## 🎨 Credits

- Game concept inspired by classic movie trivia games
- Built with ❤️ and 🐱
- Movie poster images are property of their respective studios

---

**Enjoy playing FiveCats! May the best movie buff win! 🏆🎬**