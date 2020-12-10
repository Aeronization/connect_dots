# Connect the dots game.
Simple game created by Sid Sackson.

## Description
This project was created using a websocket via Python. The server is responsible for handling the logic of the game state. I handle most validation by keeping track of the different matrix points that have been accessed to prevent line crossing.

## Rules
Rules
The game is played on a 4x4 grid of 16 nodes.
Players take turns drawing octilinear lines connecting nodes.
Each line must begin at the start or end of the existing path, so that all lines form a continuous path.
The first line may begin on any node.
A line may connect any number of nodes.
Lines may not intersect.
No node can be visited twice.
The game ends when no valid lines can be drawn.
The player who draws the last line is the loser.

## Runtime
To run this application locally follow these steps.
1) clone the repository.
2) I highly recommend a virtual environment to install the required modules.
3) Run <code>pip3 install -r requirements.txt</code> (Ensure you are in the root folder.)
4) cd into the server folder.
5) <code>python3 main.py</code>
6) open the index.html file located within the client folder in your browser.

## Hosting
I would probably use Heroku or GCP to host this project when I find time.
