# net-programming-final

[B2] Networked Number Guessing Game

**Description:**  
Create a multiplayer number guessing game where players compete to guess a secret number first, with the server providing "higher" or "lower" hints.

**Requirements:**
- ✅ Server managing multiple game rooms with 2-4 players each
- ✅ Random number generation (1-100) for each game 
- ✅ Turn-based gameplay with timeout mechanism 
- ✅ Scoring system based on number of attempts and speed 
- ❌ Game chat functionality (Chưa implement) 
- ✅ Leaderboard tracking 
- ❌ Reconnection capability if a player disconnects 
(Chưa implement) 

**Input/Output:**
- Player registration and game room selection
- Number guess input
- Server feedback on guess accuracy ("higher", "lower", "correct")
- Game status updates (current player, guesses made)
- Score reporting at the end of each round

**Example game flow:**
```
Game starting! Secret number is between 1 and 100.
Player 1's turn:
> 50
Too high! Player 2's turn.
> 25
Too low! Player 3's turn.
> 40
Too high! Player 1's turn.
> 30
Correct! Player 1 wins with 2 guesses!
```

**Deliverables:**
- Game server implementation
- Client application code
- Documentation of game protocol and mechanics
- Analysis of fairness considerations for turn-based network gameplay

## The scheme of the project may be found here : 

https://drive.google.com/file/d/1mjlh5GD-h0Dx6n3aT1rTpFfVJlkHkdyO/view?usp=sharing
