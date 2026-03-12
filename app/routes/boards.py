from flask import Blueprint, jsonify, request, url_for, abort
from flask_login import login_required, current_user
from app import db
from app.models import Board, Pin, SavedPin
from app.forms import BoardForm

boards_bp = Blueprint('boards', __name__)


@boards_bp.route('/board/<int:board_id>')
@login_required
def board_detail(board_id):
    from flask import render_template
    board = db.session.get(Board, board_id)
    if not board:
        abort(404)
    if board.is_private and board.user_id != current_user.id:
        abort(403)
    pins = board.pins.all()
    user_liked_ids = {like.pin_id for like in current_user.likes}
    user_saved_ids = {save.pin_id for save in current_user.saves}
    return render_template('board_detail.html',
        active_page='profile',
        board=board,
        pins=pins,
        user_liked_ids=user_liked_ids,
        user_saved_ids=user_saved_ids,
    )


@boards_bp.route('/board/create', methods=['POST'])
@login_required
def create_board():
    from flask import redirect, flash
    form = BoardForm()
    if form.validate_on_submit():
        board = Board(
            name=form.name.data,
            description=form.description.data,
            is_private=form.is_private.data,
            user_id=current_user.id,
        )
        db.session.add(board)
        db.session.commit()
        flash(f'Board "{board.name}" created!', 'success')
    else:
        flash('Failed to create board.', 'danger')
    from flask import url_for
    return redirect(url_for('main.user_profile', username=current_user.username))


@boards_bp.route('/board/<int:board_id>/delete', methods=['POST'])
@login_required
def delete_board(board_id):
    from flask import redirect, flash, url_for
    board = db.session.get(Board, board_id)
    if not board:
        abort(404)
    if board.user_id != current_user.id:
        abort(403)
    db.session.delete(board)
    db.session.commit()
    flash('Board deleted.', 'info')
    return redirect(url_for('main.profile'))


@boards_bp.route('/board/<int:board_id>/add/<int:pin_id>', methods=['POST'])
@login_required
def add_to_board(board_id, pin_id):
    board = db.session.get(Board, board_id)
    pin = db.session.get(Pin, pin_id)
    if not board or not pin:
        return jsonify({'ok': False, 'error': 'Not found'}), 404
    if board.user_id != current_user.id:
        return jsonify({'ok': False, 'error': 'Not your board'}), 403
    if not board.pins.filter_by(id=pin_id).first():
        board.pins.append(pin)
        db.session.commit()
        return jsonify({'ok': True, 'added': True})
    return jsonify({'ok': True, 'added': False, 'message': 'Already in board'})


@boards_bp.route('/board/<int:board_id>/remove/<int:pin_id>', methods=['POST'])
@login_required
def remove_from_board(board_id, pin_id):
    board = db.session.get(Board, board_id)
    pin = db.session.get(Pin, pin_id)
    if not board or not pin:
        return jsonify({'ok': False, 'error': 'Not found'}), 404
    if board.user_id != current_user.id:
        return jsonify({'ok': False, 'error': 'Not your board'}), 403
    if board.pins.filter_by(id=pin_id).first():
        board.pins.remove(pin)
        db.session.commit()
    return jsonify({'ok': True})


@boards_bp.route('/api/my-boards')
@login_required
def api_my_boards():
    boards = Board.query.filter_by(user_id=current_user.id).all()
    return jsonify({'boards': [{'id': b.id, 'name': b.name} for b in boards]})
