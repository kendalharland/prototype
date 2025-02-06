#!/usr/bin/python3

import curses
import subprocess
import sys
import os
import pyperclip  # Requires `pip install pyperclip`

def run_bash_script(script, input_data):
    """Runs the given Bash script with input_data as stdin and returns the output, or None if invalid."""
    try:
        if isinstance(input_data, bytes):  # Ensure input_data is a string
            input_data = input_data.decode("utf-8", errors="ignore")

        result = subprocess.run(
            ["bash", "-c", script],
            input=input_data,
            text=True,
            capture_output=True
        )

        if result.returncode == 0:  # Only return output if the command was successful
            return result.stdout
        else:
            return None  # Indicate failure
    except Exception:
        return None  # Indicate failure

def main(stdscr, stdin_data):
    # Initialize curses settings
    curses.curs_set(1)  # Show cursor
    curses.noecho()  # Prevent automatic key echo
    stdscr.keypad(True)  # Enable special keys

    height, width = stdscr.getmaxyx()
    input_box_y = height - 1
    input_text = ""
    original_output = stdin_data if stdin_data else "(No input from stdin)"
    output_text = original_output  # Start with the original output
    last_valid_output = original_output  # Track the last valid output

    prev_input_text = None
    prev_output_text = None

    while True:
        # Only redraw if input or output has changed
        if input_text != prev_input_text or output_text != prev_output_text:
            stdscr.clear()

            # Display output text
            lines = output_text.split("\n")
            for i, line in enumerate(lines[:input_box_y]):
                stdscr.addstr(i, 0, line[:width-1] + ("…" if len(line) >= width else ""))

            # Clear the input line before redrawing it
            stdscr.move(input_box_y, 0)
            stdscr.clrtoeol()
            stdscr.addstr(input_box_y, 0, "> " + input_text)
            stdscr.move(input_box_y, len(input_text) + 2)

            stdscr.refresh()  # Refresh the screen only when needed

            # Update previous values
            prev_input_text = input_text
            prev_output_text = output_text

        key = stdscr.getch()

        if key in (10, 13):  # Enter key
            break
        elif key in (127, curses.KEY_BACKSPACE, curses.KEY_DC):  # Backspace/Delete
            if input_text:
                input_text = input_text[:-1]  # Remove last character
        elif key in (curses.KEY_LEFT, curses.KEY_RIGHT, curses.KEY_UP, curses.KEY_DOWN):
            continue  # Ignore arrow keys
        elif 32 <= key <= 126:  # Printable characters
            input_text += chr(key)

        # Run the Bash script and update output
        if input_text.strip():
            new_output_text = run_bash_script(input_text, stdin_data)
            if new_output_text is not None:
                output_text = new_output_text  # Update only if valid
                last_valid_output = new_output_text  # Store last valid output
            else:
                output_text = last_valid_output  # Revert to last valid output if invalid

    # Restore terminal and copy command to clipboard
    curses.endwin()
    print(input_text, end="", flush=True, file=sys.stderr)
    #pyperclip.copy(input_text)  # Copy command to clipboard
    #print("\n(Command copied to clipboard. Paste it in your terminal to run.)", file=sys.stderr)

if __name__ == "__main__":
    # Read stdin in a blocking way
    stdin_data = sys.stdin.read() if not sys.stdin.isatty() else ""

    # Restore stdin using file descriptor 3
    os.dup2(3, 0)

    # Use curses.wrapper to initialize curses and pass stdin_data
    curses.wrapper(main, stdin_data)

