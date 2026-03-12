from flask import Blueprint, jsonify, request, flash, redirect, url_for
from flask_login import login_required, current_user
from sqlalchemy import or_
from app import db
from app.models import User, Message, Pin

messages = Blueprint('messages', __name__)


@messages.route('/messages/send', methods=['POST'])
@login_required
def send_message():
    recipient_id_raw = request.form.get("recipient_id")
    text = request.form.get("text", "").strip()
    pin_id_raw = request.form.get("pin_id")
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

    def err(msg, code=400):
        if is_ajax:
            return jsonify({"ok": False, "error": msg}), code
        flash(msg, "danger")
        return redirect(url_for("main.dashboard", tab="messages"))

    if not recipient_id_raw:
        return err("Please choose a user to message.")
    try:
        recipient_id = int(recipient_id_raw)
    except ValueError:
        return err("Invalid recipient.")
    if recipient_id == current_user.id:
        return err("You cannot message yourself.")

    recipient = db.session.get(User, recipient_id)
    if not recipient:
        return err("User not found.", 404)

    pin = None
    if pin_id_raw:
        try:
            pin = db.session.get(Pin, int(pin_id_raw))
        except ValueError:
            pass

    if not text and not pin:
        return err("Cannot send an empty message.")

    msg_obj = Message(
        sender_id=current_user.id,
        recipient_id=recipient_id,
        text=text or None,
        pin_id=pin.id if pin else None,
    )
    db.session.add(msg_obj)
    db.session.commit()

    if is_ajax:
        return jsonify({"ok": True})
    flash("Message sent.", "success")
    return redirect(url_for("main.dashboard", tab="messages", chat_with=recipient_id))


@messages.route("/api/messages_for/<int:user_id>")
@login_required
def api_messages_for(user_id):
    other = db.session.get(User, user_id)
    if not other:
        return jsonify({"error": "Not found"}), 404

    msgs = Message.query.filter(
        or_(
            (Message.sender_id == current_user.id) & (Message.recipient_id == user_id),
            (Message.sender_id == user_id) & (Message.recipient_id == current_user.id),
        )
    ).order_by(Message.created_at.asc()).all()

    # Mark incoming as read
    try:
        Message.query.filter_by(
            sender_id=user_id, recipient_id=current_user.id, is_read=False
        ).update({'is_read': True})
        db.session.commit()
    except Exception:
        db.session.rollback()

    result = []
    for m in msgs:
        result.append({
            "id": m.id,
            "from_me": m.sender_id == current_user.id,
            "text": m.text,
            "created_at": m.created_at.strftime("%H:%M"),
            "pin": {
                "id": m.pin.id,
                "title": m.pin.title,
                "description": m.pin.description,
                "image_url": url_for("static", filename="uploads/" + m.pin.image_filename)
            } if m.pin else None
        })

    return jsonify({"other_username": other.username, "messages": result})
