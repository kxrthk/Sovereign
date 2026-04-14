import sovereign_encoding  # noqa: F401 — Windows UTF-8 bootstrap (must be first)
import os

def kill_switch():
    with open("STOP.flag", "w") as f:
        f.write("TERMINATE")
    print("🚨 KILL SIGNAL SENT. BOT TERMINATING.")

if __name__ == "__main__":
    kill_switch()
