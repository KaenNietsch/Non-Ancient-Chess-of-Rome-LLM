import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from game_3d import main as run_game

if __name__ == "__main__":
    try:
        run_game()
    except KeyboardInterrupt:
        print("\nGame closed.")
        sys.exit(0)