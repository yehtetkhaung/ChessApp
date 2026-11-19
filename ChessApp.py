import os
import html
import chess
import chess.pgn
import streamlit as st
import streamlit.components.v1 as components

from ai_engine import get_best_move, evaluate_board

# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="AI Chess Arena",
    page_icon="♟️",
    layout="wide"
)

# =========================================================
# CUSTOM STYLING
# =========================================================

st.markdown("""
<style>
    .stApp {
        background-color: #161512;
        color: #f0f0f0;
    }

    .eval-box {
        padding: 15px;
        border-radius: 10px;
        background: #262421;
        border: 1px solid #49453e;
        text-align: center;
        font-size: 20px;
        font-weight: bold;
        margin-bottom: 15px;
    }

    .move-log {
        background: #262421;
        padding: 15px;
        border-radius: 10px;
        height: 320px;
        overflow-y: auto;
        font-family: monospace;
        font-size: 14px;
        line-height: 2;
        border: 1px solid #49453e;
    }

    .stButton button {
        border-radius: 8px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# =========================================================
# SESSION STATE
# =========================================================

if "board" not in st.session_state:
    st.session_state.board = chess.Board()

if "player_color" not in st.session_state:
    st.session_state.player_color = chess.WHITE

if "ai_error" not in st.session_state:
    st.session_state.ai_error = None

if "last_move_nonce" not in st.session_state:
    st.session_state.last_move_nonce = None

board = st.session_state.board

# =========================================================
# CUSTOM COMPONENT
# =========================================================

_board_component = components.declare_component(
    "chess_board_comp",
    path=os.path.join(os.path.dirname(os.path.abspath(__file__)), "chess_board_comp"),
)

# =========================================================
# HELPER FUNCTIONS
# =========================================================

def reset_game():
    st.session_state.board = chess.Board()
    st.session_state.ai_error = None
    st.session_state.last_move_nonce = None
    st.query_params.clear()

def get_move_history(board_obj):
    """Generate SAN history directly from the actual game."""
    temp_board = chess.Board()
    history = []

    for move in board_obj.move_stack:
        san = temp_board.san(move)
        history.append(san)
        temp_board.push(move)

    return history

def undo_turn():
    """Undo the previous complete player/AI turn."""
    current_board = st.session_state.board

    if not current_board.move_stack:
        return

    current_board.pop()

    while current_board.move_stack and current_board.turn != st.session_state.player_color:
        current_board.pop()

    st.session_state.ai_error = None
    st.query_params.clear()

def get_status(board_obj):
    if board_obj.is_checkmate():
        winner = "Black" if board_obj.turn == chess.WHITE else "White"
        return f"🏆 Checkmate! {winner} wins!"

    if board_obj.is_stalemate():
        return "🤝 Draw by stalemate!"

    if board_obj.is_insufficient_material():
        return "🤝 Draw by insufficient material!"

    if board_obj.is_fivefold_repetition():
        return "🤝 Draw by fivefold repetition!"

    if board_obj.is_seventyfive_moves():
        return "🤝 Draw by 75-move rule!"

    if board_obj.is_check():
        return "⚠️ Check!"

    return "Game in progress"

# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:
    st.title("⚙️ Game Settings")
    st.subheader("Player Settings")

    side_choice = st.radio(
        "Play as:",
        ["White", "Black"],
        index=0 if st.session_state.player_color == chess.WHITE else 1
    )

    new_color = chess.WHITE if side_choice == "White" else chess.BLACK

    if new_color != st.session_state.player_color:
        st.session_state.player_color = new_color
        st.session_state.ai_error = None
        st.rerun()

    st.divider()
    st.subheader("AI Difficulty")

    difficulty = st.select_slider(
        "Choose difficulty",
        options=[
            "Casual (Depth 2)",
            "Intermediate (Depth 3)",
            "Club Player (Depth 4)"
        ],
        value="Intermediate (Depth 3)"
    )

    search_depth = {
        "Casual (Depth 2)": 2,
        "Intermediate (Depth 3)": 3,
        "Club Player (Depth 4)": 4
    }[difficulty]

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🔄 New Game", use_container_width=True):
            reset_game()
            st.rerun()

    with col2:
        if st.button(
            "↩️ Undo",
            use_container_width=True,
            disabled=len(board.move_stack) == 0
        ):
            undo_turn()
            st.rerun()

    st.divider()

    game = chess.pgn.Game.from_board(board)
    exporter = chess.pgn.StringExporter(
        headers=True,
        variations=True,
        comments=True
    )
    pgn_text = game.accept(exporter)

    st.download_button(
        "📥 Download PGN",
        data=pgn_text,
        file_name="chess_game.pgn",
        mime="application/x-chess-pgn",
        use_container_width=True
    )

    st.divider()
    st.caption("AI Chess Arena")
    st.caption("Powered by Python Chess")

# =========================================================
# AI MOVE
# =========================================================

is_ai_turn = board.turn != st.session_state.player_color

if not board.is_game_over() and is_ai_turn:
    with st.spinner("🤖 AI is calculating..."):
        try:
            ai_move = get_best_move(board, depth=search_depth)

            if ai_move is not None:
                if isinstance(ai_move, str):
                    ai_move = chess.Move.from_uci(ai_move)

                if ai_move not in board.legal_moves:
                    raise ValueError("AI returned an illegal chess move.")

                board.push(ai_move)
            else:
                raise RuntimeError("AI engine did not return a move.")

            st.session_state.ai_error = None
            st.rerun()

        except Exception as e:
            st.session_state.ai_error = str(e)

# =========================================================
# MAIN INTERFACE
# =========================================================

st.title("♟️ AI Chess Arena")
st.caption("Play chess against an AI opponent using drag-and-drop controls.")

col_board, col_panel = st.columns([1.2, 0.9], gap="large")

# =========================================================
# CHESSBOARD
# =========================================================

with col_board:
    st.subheader("Chessboard")

    orientation = "white" if st.session_state.player_color == chess.WHITE else "black"
    player_turn_code = "w" if st.session_state.player_color == chess.WHITE else "b"
    can_move_now = (not board.is_game_over()) and (board.turn == st.session_state.player_color)

    move_payload = _board_component(
        fen=board.fen(),
        orientation=orientation,
        player_turn=player_turn_code,
        can_move=can_move_now,
        key="chessboard_widget",
        default=None,
    )

    if isinstance(move_payload, dict):
        nonce = move_payload.get("nonce")
        uci_move = move_payload.get("uci", "")

        if nonce and nonce != st.session_state.last_move_nonce:
            st.session_state.last_move_nonce = nonce
            try:
                move = chess.Move.from_uci(uci_move)
                if move in board.legal_moves and board.turn == st.session_state.player_color:
                    board.push(move)
                    st.session_state.ai_error = None
                    st.rerun()
            except (ValueError, TypeError):
                pass

# =========================================================
# RIGHT PANEL
# =========================================================

with col_panel:
    st.subheader("Game Information")

    try:
        raw_eval = evaluate_board(board) / 100.0
        eval_text = f"+{raw_eval:.2f}" if raw_eval > 0 else f"{raw_eval:.2f}"
    except Exception:
        eval_text = "Unavailable"

    st.markdown(
        f"""
        <div class="eval-box">
            Engine Evaluation: {eval_text}
        </div>
        """,
        unsafe_allow_html=True
    )

    status = get_status(board)

    if board.is_checkmate():
        st.error(status)
    elif board.is_game_over():
        st.warning(status)
    elif board.is_check():
        st.warning(status)
    elif st.session_state.ai_error:
        st.error("AI Engine Error: " + str(st.session_state.ai_error))
    else:
        if board.turn == st.session_state.player_color:
            st.success("🎯 Your Turn")
        else:
            st.info("🤖 AI's Turn")

    st.markdown("### Position Information")
    st.write("Current turn:", "White" if board.turn == chess.WHITE else "Black")
    st.write("Move number:", board.fullmove_number)
    st.write("Moves played:", len(board.move_stack))

    st.markdown("### 📜 Move History")

    history = get_move_history(board)
    rows = []

    for i in range(0, len(history), 2):
        move_number = (i // 2) + 1
        white_move = history[i]
        black_move = history[i + 1] if i + 1 < len(history) else ""
        rows.append(f"{move_number:>2}. {white_move:<9} {black_move}")

    log_content = (
        "<br>".join(html.escape(row) for row in rows)
        if rows
        else "<i>No moves played yet.</i>"
    )

    st.markdown(
        f"""
        <div class="move-log">
            {log_content}
        </div>
        """,
        unsafe_allow_html=True
    )

    with st.expander("View FEN position"):
        st.code(board.fen(), language="text")

# =========================================================
# FOOTER
# =========================================================

st.divider()
st.caption("AI Chess Arena | Built with Streamlit, Python-Chess and JavaScript")
