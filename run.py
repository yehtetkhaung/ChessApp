import os
import sys
from streamlit.web import cli as stcli


def app_path(filename: str) -> str:
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, filename)


if __name__ == "__main__":
    sys.argv = ["streamlit", "run", app_path("ChessApp.py")]
    sys.exit(stcli.main())
