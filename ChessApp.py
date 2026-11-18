import streamlit as st
import chess
import chess.pgn
import streamlit.components.v1 as components
from ai_engine import get_best_move, evaluate_board

st.set_page_config(page_title="Drag-and-Drop AI Chess", page_icon="♟️", layout="wide")

# Custom UI Styling
st.markdown("""
<style>
    .stApp { background-color: #161512; color: #f0f0f0; }
    .eval-box {
        padding: 10px 15px; border-radius: 8px; background-color: #262421;
        border: 1px solid #3d3a35; text-align: center; font-weight: bold; margin-bottom: 10px;
    }
    .move-log {
        background-color: #262421; padding: 12px; border-radius: 8px;
        height: 320px; overflow-y: auto; font-family: monospace; font-size: 14px;
        border: 1px solid #3d3a35;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "board" not in st.session_state:
    st.session_state.board = chess.Board()
if "move_history" not in st.session_state:
    st.session_state.move_history = []
if "player_color" not in st.session_state:
    st.session_state.player_color = chess.WHITE

board: chess.Board = st.session_state.board

# Check for incoming drag-and-drop move from URL params
params = st.query_params
if "move" in params:
    uci_move = params["move"]
    try:
        move = chess.Move.from_uci(uci_move)
        if move in board.legal_moves:
            san = board.san(move)
            board.push(move)
            st.session_state.move_history.append(san)
            st.query_params.clear()
            st.rerun()
    except Exception:
        st.query_params.clear()

# --- SIDEBAR CONTROLS ---
with st.sidebar:
    st.title("⚙️ Game Settings")
    
    side_choice = st.radio("Play As:", ["White", "Black"], index=0 if st.session_state.player_color == chess.WHITE else 1)
    new_color = chess.WHITE if side_choice == "White" else chess.BLACK
    if new_color != st.session_state.player_color:
        st.session_state.player_color = new_color
        st.rerun()

    difficulty = st.select_slider(
        "AI Difficulty",
        options=["Casual (Depth 2)", "Intermediate (Depth 3)", "Club Player (Depth 4)"],
        value="Intermediate (Depth 3)"
    )
    search_depth = {"Casual (Depth 2)": 2, "Intermediate (Depth 3)": 3, "Club Player (Depth 4)": 4}[difficulty]

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 New Game", use_container_width=True):
            st.session_state.board = chess.Board()
            st.session_state.move_history = []
            st.query_params.clear()
            st.rerun()
    with col2:
        if st.button("↩️ Undo Move", use_container_width=True, disabled=len(board.move_stack) < 2):
            board.pop()
            board.pop()
            if len(st.session_state.move_history) >= 2:
                st.session_state.move_history = st.session_state.move_history[:-2]
            st.query_params.clear()
            st.rerun()

    st.divider()
    game_pgn = str(chess.pgn.Game.from_board(board))
    st.download_button("📥 Download PGN", game_pgn, "chess_game.pgn", "text/plain", use_container_width=True)

# --- TRIGGER AI MOVE IF IT'S AI's TURN ---
is_ai_turn = board.turn != st.session_state.player_color
if not board.is_game_over() and is_ai_turn:
    with st.spinner("🤖 AI is calculating best move..."):
        ai_move = get_best_move(board, depth=search_depth)
        if ai_move:
            san = board.san(ai_move)
            board.push(ai_move)
            st.session_state.move_history.append(san)
            st.rerun()

# --- MAIN LAYOUT ---
st.title("♟️ Interactive Drag-and-Drop Chess AI")

col_board, col_panel = st.columns([1.2, 1], gap="large")

with col_board:
    fen = board.fen()
    board_orientation = "white" if st.session_state.player_color == chess.WHITE else "black"
    
    # Use regular string with .replace() to avoid f-string curly brace collisions with JavaScript
    chessboard_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <link rel="stylesheet" href="https://unpkg.com/@chrisoakman/chessboardjs@1.0.0/dist/chessboard-1.0.0.min.css" />
        <script src="https://code.jquery.com/jquery-3.5.1.min.js"></script>
        <script src="https://unpkg.com/@chrisoakman/chessboardjs@1.0.0/dist/chessboard-1.0.0.min.js"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/chess.js/0.10.3/chess.min.js"></script>
    </head>
    <body style="background-color: #161512; display: flex; justify-content: center;">
        <div id="board" style="width: 480px"></div>
        <script>
            var board = null;
            var game = new Chess('__FEN__');

            function onDragStart (source, piece, position, orientation) {
                if (game.game_over()) return false;
                if ((game.turn() === 'w' && piece.search(/^b/) !== -1) ||
                    (game.turn() === 'b' && piece.search(/^w/) !== -1)) {
                    return false;
                }
            }

            function onDrop (source, target) {
                var move = game.move({
                    from: source,
                    to: target,
                    promotion: 'q'
                });

                if (move === null) return 'snapback';
                window.parent.location.search = '?move=' + source + target;
            }

            function onSnapEnd () {
                board.position(game.fen());
            }

            var config = {
                draggable: true,
                position: '__FEN__',
                orientation: '__ORIENTATION__',
                pieceTheme: 'https://unpkg.com/@chrisoakman/chessboardjs@1.0.0/dist/img/chesspieces/wikipedia/{piece}.png',
                onDragStart: onDragStart,
                onDragStart: onDragStart,
                onDrop: onDrop,
                onSnapEnd: onSnapEnd
            }
            board = Chessboard('board', config);
        </script>
    </body>
    </html>
    """.replace("__FEN__", fen).replace("__ORIENTATION__", board_orientation)
    
    components.html(chessboard_html, height=510)

with col_panel:
    raw_eval = evaluate_board(board) / 100.0
    eval_text = f"+{raw_eval:.2f}" if raw_eval > 0 else f"{raw_eval:.2f}"
    st.markdown(f'<div class="eval-box">Engine Evaluation: {eval_text}</div>', unsafe_allow_html=True)

    if board.is_checkmate():
        winner = "Black" if board.turn == chess.WHITE else "White"
        st.error(f"🏆 Checkmate! {winner} wins!")
    elif board.is_stalemate():
        st.warning("🤝 Draw by Stalemate!")
    elif board.is_check():
        st.warning("⚠️ Check!")
    else:
        status = "Your Turn" if not is_ai_turn else "AI is thinking..."
        st.info(f"🎯 Status: {status}")

    st.subheader("📜 Move History")
    history = st.session_state.move_history
    rows = []
    for i in range(0, len(history), 2):
        num = (i // 2) + 1
        w = history[i]
        b = history[i + 1] if i + 1 < len(history) else ""
        rows.append(f"{num:>2}. {w:<8} {b}")
    log_content = "<br>".join(rows) if rows else "<i>No moves played yet. Drag a piece to start!</i>"
    st.markdown(f'<div class="move-log">{log_content}</div>', unsafe_allow_html=True)
