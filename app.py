#!/usr/bin/env python3
"""CLI Workout Tool -- adaptive home training with fancy ASCII animations."""

from workout_cli.menus import main
from workout_cli.config import console, C_REST

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print(
            f"\n\n  [{C_REST}]Stopped. Progress saved up to last "
            f"completed session.[/{C_REST}]\n")
