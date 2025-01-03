# Slime Run Game

**Slime Run** is an engaging and challenging 2D game developed using Python and Pygame where players navigate through a world filled with obstacles, ropes, tentacles, and coins, while being guided by a sophisticated Fuzzy Alert system. The objective is to collect coins and reach the goal while avoiding or navigating through various threats.

## Table of Contents

1. [Game Features](#game-features)
2. [Installation](#installation)
3. [Gameplay](#gameplay)
4. [Code Overview](#code-overview)
5. [Licenses](#licenses)

## Game Features

- **Dynamic Environment:** Navigate through obstacles and interacting objects, like ropes and tentacles.
- **Sophisticated AI:** The game features intelligent entities such as smart ropes and tentacles that learn and adapt behaviors using Q-learning.
- **Fuzzy Logic System:** Implemented to provide an alertness score based on proximity and speed of nearby threats (like ropes or tentacles).
- **Multiple Levels of Difficulty:** Choose from Easy, Medium, and Hard settings.
- **Responsive Camera:** Smoothly follows the player as they move throughout the world.
- **Main Menu and UI:** A simple and intuitive user interface to start the game and change difficulty settings.

## Installation

Ensure Python 3.x and Pygame library are installed on your machine before running the game. You can install the Pygame library using pip:

```sh
pip install pygame
```

Clone this repository and navigate into its directory:

```sh
git clone <repository-url>
cd <repository-name>
```

To start the game, run the following command:

```sh
python main.py
```

## Gameplay

- Control the chain by clicking within the "Start Area" to initiate movement.
- Avoid contact with ropes and tentacles, while aiming to pick up and hold the coin to the goal area.
- Monitor the alert system which dynamically dims the screen with red tint based on immediate threats from ropes or tentacles.
- Completing the level requires successfully navigating the chain to the "End Area" with the coin.

## Code Overview

### Main Components

- **`main.py`:** Entry point of the game. Handles the game loop and user interactions.
- **`alert.py`:** Implements a fuzzy logic-based alert system to determine the danger level and displays an overlay.
- **`camera.py`:** Manages the camera view to follow the player smoothly.
- **`game_elements`:** Contains files like Chain, Coin, SmartBlueTentacle, and SmartVerletRope, which are objects the player interacts with.
- **`menu_and_difficulty`:** Code for the main menu and difficulty setting via button interactions.
- **`slow_verlet_rope.py` and `smart_blue_tentacle.py`:** Define intelligent behavior of ropes and tentacles using Q-Learning.
- **`slime_obstacle.py`:** Defines slime obstacles with dynamics that pulse and wobble.
- **`rope_optimizer.py`:** Manages rope configurations through evolutionary strategies within the game world.
- **`slime_obstacle.py`:** Manages the slime obstacles in the world.

### Key Concepts

- **Q-Learning:** Used in `smart_blue_tentacle.py` and `slow_verlet_rope.py` to facilitate adaptive learning behavior based on the player's actions.
- **Fuzzy Logic:** Drives the threat alert system for enhanced immersion and player feedback.

## Licenses

This project is licensed under the MIT License. See the `LICENSE` file for more details.

Please feel free to contribute, give feedback, or suggest new features!