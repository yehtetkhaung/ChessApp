import streamlit as st
import chess
import chess.svg
import chess.pgn
import base64
import io
from ai_engine import get_best_move, evaluate_board

st.set_page_config(page_title="Grandmaster AI Chess", page_icon="♟️", layout="wide")

# Custom CSS for clean dark/modern chess aesthetic
st.markdown("""
<style>
    .stApp {
        background-color: #161512;
        color: #f0f0f0;
    }
    .eval-box {
        padding: 10px 15px;
        border-radius: 8px;
        background-color: #262421;
        border: 1px solid #3d3a35;
        text-align: center;
        font-weight: bold;
        margin-bottom: 10px;
    }
    .captured-box {
        padding: 8px 12px;
        border-radius: 6px;
        background-color: #201e1b;
        min-height: 40px;
        font-size: 22px;
        letter-spacing: 2px;
    }
    .move-log {
        background-color: #262421;
        padding: 12px;
        border-radius: 8px;
        height: 260px;
        overflow-y: auto;
        font-family: monospace;
        font-size: 14px;
        border: 1px solid #3d3a35;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "board" not in st.session_state:
    st.session_state.board = chess.Board()
if "player_color" not in st.session_state:
    st.session_state.player_color = chess.WHITE
if "move_history" not in st.session_state:
    st.session_state.move_history = []
if "last_move" not in st.session_state:
    st.session_state.last_move = None
if "selected_square" not in st.session_state:
    st.session_state.selected_square = None

board: chess.Board = st.session_state.board

UNICODE_PIECES = {
    'P': '♙', 'N': '♘', 'B': '♗', 'R': '♖', 'Q': '♕', 'K': '♔',
    'p': '♟', 'n': '♞', 'b': '♝', 'r': '♜', 'q': '♛', 'k': '♚'
}


def get_captured_pieces(board: chess.Board):
    initial = {'P': 8, 'N': 2, 'B': 2, 'R': 2, 'Q': 1,
               'p': 8, 'n': 2, 'b': 2, 'r': 2, 'q': 1}
    current = {}
    for sq in chess.SQUARES:
        p = board.piece_at(sq)
        if p:
            sym = p.symbol()
            current[sym] = current.get(sym, 0) + 1

    white_captured = []  # Black pieces captured by White
    black_captured = []  # White pieces captured by Black

    for sym, count in initial.items():
        diff = count - current.get(sym, 0)
        if diff > 0:
            if sym.islower():
                white_captured.extend([UNICODE_PIECES[sym]] * diff)
            else:
                black_captured.extend([UNICODE_PIECES[sym]] * diff)
    return "".join(white_captured), "".join(black_captured)


def render_svg_board(board: chess.Board, flipped: bool, last_move, selected_sq):
    squares = {}
    if selected_sq is not None:
        squares[selected_sq] = "#f6f669cc"
        for move in board.legal_moves:
            if move.from_square == selected_sq:
                squares[move.to_square] = "#829769aa"

    svg_code = chess.svg.board(
        board=board,
        size=520,
        flipped=flipped,
        lastmove=last_move,
        squares=squares,
        check=board.king(board.turn) if board.is_check() else None,
        colors={
            "square light": "#eeeed2",
            "square dark": "#769656",
            "square light lastmove": "#f6f669",
            "square dark lastmove": "#baca2b",
        }
    )
    b64 = base64.b64encode(svg_code.encode("utf-8")).decode("utf-8")
    return f'<div style="display:flex; justify-content:center;"><img src="data:image/svg+xml;base64,{b64}" style="border-radius: 8px; box-shadow: 0 8px 24px rgba(0,0,0,0.5); max-width: 100%;"/></div>'


# --- SIDEBAR SETTINGS ---
with st.sidebar:
    st.title("⚙️ Game Settings")

    side_choice = st.radio("Play As:", ["White", "Black"], index=0 if st.session_state.player_color == chess.WHITE else 1)
    chosen_color = chess.WHITE if side_choice == "White" else chess.BLACK

    difficulty = st.select_slider(
        "AI Difficulty",
        options=["Casual (Depth 2)", "Intermediate (Depth 3)", "Club Player (Depth 4)"],
        value="Intermediate (Depth 3)"
    )
    depth_map = {"Casual (Depth 2)": 2, "Intermediate (Depth 3)": 3, "Club Player (Depth 4)": 4}
    search_depth = depth_map[difficulty]

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("🔄 New Game", use_container_width=True):
            st.session_state.board = chess.Board()
            st.session_state.player_color = chosen_color
            st.session_state.move_history = []
            st.session_state.last_move = None
            st.session_state.selected_square = None
            st.rerun()

    with col_btn2:
        if st.button("↩️ Undo Move", use_container_width=True, disabled=len(board.move_stack) < 2):
            board.pop()
            board.pop()
            if len(st.session_state.move_history) >= 2:
                st.session_state.move_history = st.session_state.move_history[:-2]
            st.session_state.last_move = board.peek() if board.move_stack else None
            st.session_state.selected_square = None
            st.rerun()

    st.divider()
    # Export PGN
    game_pgn = chess.pgn.Game.from_board(board)
    pgn_str = str(game_pgn)
    st.download_button(
        label="📥 Download PGN",
        data=pgn_str,
        file_name="chess_game.pgn",
        mime="text/plain",
        use_container_width=True
    )

# --- TRIGGER AI MOVE IF IT IS AI'S TURN ---
if not board.is_game_over() and board.turn != st.session_state.player_color:
    with st.spinner("🤖 AI is calculating best move..."):
        ai_move = get_best_move(board, depth=search_depth)
        if ai_move:
            san = board.san(ai_move)
            board.push(ai_move)
            st.session_state.last_move = ai_move
            st.session_state.move_history.append(san)
            st.session_state.selected_square = None
            st.rerun()

# --- MAIN LAYOUT ---
st.title("♟️ Interactive AI Chess Arena")

left_col, right_col = st.columns([1.3, 1], gap="large")

with left_col:
    white_cap, black_cap = get_captured_pieces(board)
    top_cap = black_cap if st.session_state.player_color == chess.WHITE else white_cap
    bottom_cap = white_cap if st.session_state.player_color == chess.WHITE else black_cap

    st.markdown(f'<div class="captured-box">AI Captures: {top_cap or "—"}</div>', unsafe_allow_html=True)
    st.markdown(
        render_svg_board(
            board,
            flipped=(st.session_state.player_color == chess.BLACK),
            last_move=st.session_state.last_move,
            selected_sq=st.session_state.selected_square
        ),
        unsafe_allow_html=True
    )
    st.markdown(f'<div class="captured-box" style="margin-top:8px;">Your Captures: {bottom_cap or "—"}</div>', unsafe_allow_html=True)

with right_col:
    # Position Evaluation Bar / Readout
    raw_eval = evaluate_board(board) / 100.0
    eval_display = f"+{raw_eval:.2f}" if raw_eval > 0 else f"{raw_eval:.2f}"
    st.markdown(f'<div class="eval-box">Engine Evaluation: {eval_display}</div>', unsafe_allow_html=True)

    # Game Status Banner
    if board.is_checkmate():
        winner = "Black" if board.turn == chess.WHITE else "White"
        st.error(f"🏆 Checkmate! {winner} wins!")
    elif board.is_stalemate():
        st.warning("🤝 Draw by Stalemate!")
    elif board.is_insufficient_material():
        st.warning("🤝 Draw by Insufficient Material!")
    elif board.is_check():
        st.warning("⚠️ Check!")
    else:
        turn_label = "Your Turn" if board.turn == st.session_state.player_color else "AI's Turn"
        st.info(f"🎯 Status: {turn_label}")

    # Visual Interactive Move Selector (No typing required!)
    if not board.is_game_over() and board.turn == st.session_state.player_color:
        st.subheader("Make Your Move")

        # Group legal moves by piece origin square
        legal_moves = list(board.legal_moves)
        origin_squares = sorted(list(set(m.from_square for m in legal_moves)))

        def format_origin(sq):
            piece = board.piece_at(sq)
            sym = UNICODE_PIECES[piece.symbol()] if piece else ""
            return f"{sym} {chess.square_name(sq).upper()}"

        selected_origin = st.selectbox(
            "1. Select Piece to Highlight Legal Moves:",
            options=origin_squares,
            format_func=format_origin,
            key="piece_selector"
        )

        # Highlight selected square on the SVG board immediately
        if st.session_state.selected_square != selected_origin:
            st.session_state.selected_square = selected_origin
            st.rerun()

        # Filter target moves for that selected piece
        piece_moves = [m for m in legal_moves if m.from_square == selected_origin]

        def format_move(m: chess.Move):
            san = board.san(m)
            dest = chess.square_name(m.to_square).upper()
            capture_tag = " (Capture)" if board.is_capture(m) else ""
            promo_tag = f" (Promote to {chess.piece_name(m.promotion).title()})" if m.promotion else ""
            return f"{san} → {dest}{capture_tag}{promo_tag}"

        chosen_move = st.selectbox(
            "2. Choose Destination:",
            options=piece_moves,
            format_func=format_move
        )

        if st.button("✅ Play Move", type="primary", use_container_width=True):
            san = board.san(chosen_move)
            board.push(chosen_move)
            st.session_state.last_move = chosen_move
            st.session_state.move_history.append(san)
            st.session_state.selected_square = None
            st.rerun()

    # Move History Log
    st.subheader("📜 Move History")
    history = st.session_state.move_history
    formatted_rows = []
    for i in range(0, len(history), 2):
        move_num = (i // 2) + 1
        w_move = history[i]
        b_move = history[i + 1] if i + 1 < len(history) else ""
        formatted_rows.append(f"{move_num:>2}. {w_move:<8} {b_move}")

    log_html = "<br>".join(formatted_rows) if formatted_rows else "<i>No moves played yet.</i>"
    st.markdown(f'<div class="move-log">{log_html}</div>', unsafe_allow_html=True)
