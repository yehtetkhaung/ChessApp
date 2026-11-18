import streamlit as st
import chess
import chess.engine
import shutil
import subprocess
import os

st.set_page_config(page_title="AI Chess App (Intermediate)", page_icon="♟️", layout="centered")

st.title("♟️ Play Chess vs AI (Intermediate Level)")
st.write("Play a game of chess against an intermediate-strength AI bot (~1500 Elo). Enter moves in standard UCI notation (e.g., `e2e4`, `g1f3`).")

# Locate or download stockfish fallback handling for cloud deployment
@st.cache_resource
def get_stockfish_path():
    # Streamlit Cloud Linux environment typically has stockfish available via apt, 
    # or we check local path.
    path = shutil.which("stockfish")
    if path:
        return path
    # Fallback paths if needed
    if os.path.exists("/usr/games/stockfish"):
        return "/usr/games/stockfish"
    return "stockfish"

stockfish_path = get_stockfish_path()

# Initialize chess board in session state
if "board" not in st.session_state:
    st.session_state.board = chess.Board()

board = st.session_state.board

# Sidebar controls
with st.sidebar:
    st.header("Game Controls")
    if st.button("🔄 Reset Game"):
        st.session_state.board = chess.Board()
        st.rerun()
    
    st.info("AI Difficulty: Intermediate (~1500 Elo)")
    ai_skill = st.slider("AI Skill Level (1-20)", min_value=1, max_value=20, value=10)

# Display current board state as FEN and text/ascii fallback or graphic
st.text(f"Current FEN: {board.fen()}")

# Visual board representation using markdown/fen
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Board State")
    # Render standard chessboard view using standard ascii or fen visualization
    board_html = board.fen()
    st.code(str(board), language=None)

with col2:
    st.subheader("Game Status")
    if board.is_checkmate():
        st.error("Checkmate! Game Over.")
    elif board.is_stalemate():
        st.warning("Stalemate! It's a draw.")
    elif board.is_check():
        st.warning("⚠️ Check!")
    else:
        st.success("Game in progress. Your turn (White).")

# Move input form for user
with st.form(key="move_form", clear_on_submit=True):
    user_move_input = st.text_input("Enter your move (e.g., e2e4):", "")
    submit_button = st.form_submit_button(label="Make Move")

if submit_button and user_move_input:
    try:
        user_move = chess.Move.from_uci(user_move_input.strip())
        if user_move in board.legal_moves:
            board.push(user_move)
            st.rerun()
        else:
            st.error("Illegal move! Try again.")
    except ValueError:
        st.error("Invalid format! Use UCI notation like `e2e4`.")

# Trigger AI Move if it's Black's turn and game is not over
if not board.is_game_over() and board.turn == chess.BLACK:
    with st.spinner("AI is thinking..."):
        try:
            with chess.engine.SimpleEngine.popen_spawn(stockfish_path) as engine:
                # Set intermediate skill level (Skill level 10 ~ 1500 Elo)
                engine.configure({"Skill Level": ai_skill})
                result = engine.play(board, chess.engine.Limit(time=1.0))
                board.push(result.move)
                st.rerun()
        except Exception as e:
            st.error(f"Error running Stockfish engine: {e}")
            st.markdown("*Tip: Ensure Stockfish binary is installed on your system or environment.*")