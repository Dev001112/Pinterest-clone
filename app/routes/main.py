from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify, abort
from flask_login import login_required, current_user
from sqlalchemy import or_, func, desc
from datetime import datetime, timedelta
from app import db
from app.models import User, Pin, Message, Like, SavedPin, Comment, Board, Tag, Notification, pin_tags
from app.forms import PinForm, PinEditForm, CommentForm, BoardForm, EditProfileForm, SettingsForm
import os, uuid
from werkzeug.utils import secure_filename
from PIL import Image

main = Blueprint('main', __name__)


def compress_and_save_image(image_obj, filename, folder, max_size=(1200, 1200), quality=85):
    filepath = os.path.join(folder, filename)
    img = Image.open(image_obj)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    img.thumbnail(max_size)
    img.save(filepath, optimize=True, quality=quality)
    return filepath


def get_popular_tags(limit=20):
    try:
        return db.session.query(Tag, func.count(pin_tags.c.pin_id).label("cnt"))\
            .join(pin_tags, Tag.id == pin_tags.c.tag_id)\
            .group_by(Tag.id)\
            .order_by(desc("cnt"))\
            .limit(limit).all()
    except Exception:
        return []


# ─── Root ────────────────────────────────────────────────────────────────────

@main.route('/')
def root():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))


# ─── Dashboard ───────────────────────────────────────────────────────────────

@main.route('/dashboard')
@login_required
def dashboard():
    active_tab = request.args.get('tab', 'home')
    page = request.args.get('page', 1, type=int)
    tag_filter = request.args.get('tag', '')
    chat_with_id = request.args.get('chat_with', type=int)
    share_pin_id = request.args.get('share_pin', type=int)

    query = Pin.query
    if tag_filter:
        query = query.join(Pin.tags).filter(Tag.name == tag_filter.lower())
    pins = query.order_by(Pin.created_at.desc()).paginate(page=page, per_page=20)

    users = User.query.filter(User.id != current_user.id).all()

    chat_with_user = db.session.get(User, chat_with_id) if chat_with_id else None
    conversation_messages = []
    if chat_with_user:
        conversation_messages = Message.query.filter(
            or_(
                (Message.sender_id == current_user.id) & (Message.recipient_id == chat_with_id),
                (Message.sender_id == chat_with_id) & (Message.recipient_id == current_user.id),
            )
        ).order_by(Message.created_at.asc()).all()
        try:
            Message.query.filter_by(
                sender_id=chat_with_id, recipient_id=current_user.id, is_read=False
            ).update({'is_read': True})
            db.session.commit()
        except Exception:
            db.session.rollback()

    contact_ids = set()
    for m in Message.query.filter(
        or_(Message.sender_id == current_user.id, Message.recipient_id == current_user.id)
    ).all():
        contact_ids.add(m.recipient_id if m.sender_id == current_user.id else m.sender_id)
    contacts = User.query.filter(User.id.in_(contact_ids)).all() if contact_ids else []

    share_pin = db.session.get(Pin, share_pin_id) if share_pin_id else None
    user_liked_ids = {like.pin_id for like in current_user.likes}
    user_saved_ids = {save.pin_id for save in current_user.saves}
    popular_tags = get_popular_tags(20)

    return render_template(
        "dashboard.html",
        active_page='home',
        pins=pins.items,
        page=pins.page,
        has_next=pins.has_next,
        users=users,
        active_tab=active_tab,
        chat_with_user=chat_with_user,
        messages=conversation_messages,
        contacts=contacts,
        share_pin=share_pin,
        user_liked_ids=user_liked_ids,
        user_saved_ids=user_saved_ids,
        pin_form=PinForm(),
        board_form=BoardForm(),
        popular_tags=popular_tags,
        tag_filter=tag_filter,
    )


# ─── Explore ─────────────────────────────────────────────────────────────────

@main.route('/explore')
@login_required
def explore():
    week_ago = datetime.utcnow() - timedelta(days=7)
    trending_subq = db.session.query(
        Pin.id, func.count(Like.id).label('lc')
    ).outerjoin(Like).filter(Pin.created_at >= week_ago).group_by(Pin.id).subquery()

    trending_pins = db.session.query(Pin)\
        .join(trending_subq, Pin.id == trending_subq.c.id)\
        .order_by(desc(trending_subq.c.lc))\
        .limit(30).all()

    popular_tags = get_popular_tags(40)
    user_liked_ids = {like.pin_id for like in current_user.likes}
    user_saved_ids = {save.pin_id for save in current_user.saves}

    return render_template('explore.html',
        active_page='explore',
        trending_pins=trending_pins,
        popular_tags=popular_tags,
        user_liked_ids=user_liked_ids,
        user_saved_ids=user_saved_ids,
    )


# ─── Following Feed ───────────────────────────────────────────────────────────

@main.route('/following-feed')
@login_required
def following_feed():
    page = request.args.get('page', 1, type=int)
    followed_ids = [u.id for u in current_user.followed.all()]
    if followed_ids:
        result = Pin.query.filter(Pin.user_id.in_(followed_ids))\
            .order_by(Pin.created_at.desc()).paginate(page=page, per_page=20)
        pins, has_next = result.items, result.has_next
    else:
        pins, has_next = [], False

    user_liked_ids = {like.pin_id for like in current_user.likes}
    user_saved_ids = {save.pin_id for save in current_user.saves}

    return render_template('following_feed.html',
        active_page='following',
        pins=pins, has_next=has_next, page=page,
        user_liked_ids=user_liked_ids,
        user_saved_ids=user_saved_ids,
    )


# ─── Pins ─────────────────────────────────────────────────────────────────────

@main.route('/upload', methods=['POST'])
@login_required
def upload_pin():
    form = PinForm()
    if form.validate_on_submit():
        image = form.image.data
        ext = secure_filename(image.filename).rsplit('.', 1)[-1].lower()
        filename = f"{uuid.uuid4().hex}.{ext}"
        folder = current_app.config['UPLOAD_FOLDER']
        os.makedirs(folder, exist_ok=True)
        compress_and_save_image(image, filename, folder)

        pin = Pin(
            title=form.title.data,
            description=form.description.data,
            image_filename=filename,
            source_url=form.source_url.data or None,
            author=current_user,
        )
        if form.tags.data:
            for name in [t.strip().lower() for t in form.tags.data.split(',') if t.strip()]:
                tag = Tag.query.filter_by(name=name).first() or Tag(name=name)
                if not tag.id:
                    db.session.add(tag)
                pin.tags.append(tag)

        db.session.add(pin)
        db.session.commit()
        flash('Pin uploaded!', 'success')
    else:
        for field, errors in form.errors.items():
            for e in errors:
                flash(f"{field}: {e}", 'danger')
    return redirect(url_for('main.dashboard', tab='home'))


@main.route('/pin/<int:pin_id>')
@login_required
def pin_detail(pin_id):
    pin = db.session.get(Pin, pin_id)
    if not pin:
        abort(404)
    pin.views = (pin.views or 0) + 1
    db.session.commit()

    related = Pin.query.join(Pin.tags).filter(
        Tag.id.in_([t.id for t in pin.tags.all()]), Pin.id != pin.id
    ).distinct().limit(6).all()

    return render_template('pin_detail.html',
        active_page='',
        pin=pin,
        form=CommentForm(),
        related_pins=related,
        user_liked=Like.query.filter_by(user_id=current_user.id, pin_id=pin.id).first() is not None,
        user_saved=SavedPin.query.filter_by(user_id=current_user.id, pin_id=pin.id).first() is not None,
        likes_count=len(pin.likes),
    )


@main.route('/pin/<int:pin_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_pin(pin_id):
    pin = db.session.get(Pin, pin_id)
    if not pin:
        abort(404)
    if pin.author != current_user:
        abort(403)
    form = PinEditForm(obj=pin)
    if request.method == 'GET':
        form.tags.data = ', '.join(t.name for t in pin.tags.all())
    if form.validate_on_submit():
        pin.title = form.title.data
        pin.description = form.description.data
        pin.source_url = form.source_url.data or None
        pin.tags = []
        if form.tags.data:
            for name in [t.strip().lower() for t in form.tags.data.split(',') if t.strip()]:
                tag = Tag.query.filter_by(name=name).first() or Tag(name=name)
                if not tag.id:
                    db.session.add(tag)
                pin.tags.append(tag)
        db.session.commit()
        flash('Pin updated!', 'success')
        return redirect(url_for('main.pin_detail', pin_id=pin.id))
    return render_template('edit_pin.html', active_page='', form=form, pin=pin)


@main.route('/pin/<int:pin_id>/delete', methods=['POST'])
@login_required
def delete_pin(pin_id):
    pin = db.session.get(Pin, pin_id)
    if not pin:
        abort(404)
    if pin.author != current_user:
        abort(403)
    img_path = os.path.join(current_app.config['UPLOAD_FOLDER'], pin.image_filename)
    if os.path.exists(img_path):
        os.remove(img_path)
    db.session.delete(pin)
    db.session.commit()
    flash('Pin deleted.', 'info')
    return redirect(url_for('main.dashboard'))


# ─── Like / Save ──────────────────────────────────────────────────────────────

@main.route('/pin/<int:pin_id>/like', methods=['POST'])
@login_required
def like_pin(pin_id):
    pin = db.session.get(Pin, pin_id)
    if not pin:
        return jsonify({'ok': False}), 404
    existing = Like.query.filter_by(user_id=current_user.id, pin_id=pin.id).first()
    if existing:
        db.session.delete(existing)
        liked = False
    else:
        db.session.add(Like(user_id=current_user.id, pin_id=pin.id))
        liked = True
        if pin.author != current_user:
            if not Notification.query.filter_by(
                user_id=pin.user_id, actor_id=current_user.id, type='like', pin_id=pin.id
            ).first():
                db.session.add(Notification(
                    user_id=pin.user_id, actor_id=current_user.id, type='like', pin_id=pin.id
                ))
    db.session.commit()
    return jsonify({"ok": True, "liked": liked, "count": Like.query.filter_by(pin_id=pin.id).count()})


@main.route('/pin/<int:pin_id>/save', methods=['POST'])
@login_required
def save_pin(pin_id):
    pin = db.session.get(Pin, pin_id)
    if not pin:
        return jsonify({'ok': False}), 404
    existing = SavedPin.query.filter_by(user_id=current_user.id, pin_id=pin.id).first()
    if existing:
        db.session.delete(existing)
        saved = False
    else:
        db.session.add(SavedPin(user_id=current_user.id, pin_id=pin.id))
        saved = True
    db.session.commit()
    return jsonify({"ok": True, "saved": saved})


# ─── Comments ────────────────────────────────────────────────────────────────

@main.route('/pin/<int:pin_id>/comment', methods=['POST'])
@login_required
def comment(pin_id):
    pin = db.session.get(Pin, pin_id)
    if not pin:
        abort(404)
    form = CommentForm()
    if form.validate_on_submit():
        c = Comment(text=form.text.data, user_id=current_user.id, pin_id=pin.id)
        db.session.add(c)
        if pin.author != current_user:
            db.session.add(Notification(
                user_id=pin.user_id, actor_id=current_user.id, type='comment', pin_id=pin.id
            ))
        db.session.commit()
        flash('Comment posted!', 'success')
    return redirect(url_for('main.pin_detail', pin_id=pin.id))


@main.route('/comment/<int:comment_id>/delete', methods=['POST'])
@login_required
def delete_comment(comment_id):
    c = db.session.get(Comment, comment_id)
    if not c:
        abort(404)
    pin = db.session.get(Pin, c.pin_id)
    if c.user_id != current_user.id and (not pin or pin.author != current_user):
        abort(403)
    pin_id = c.pin_id
    db.session.delete(c)
    db.session.commit()
    flash('Comment deleted.', 'info')
    return redirect(url_for('main.pin_detail', pin_id=pin_id))


# ─── Profile ──────────────────────────────────────────────────────────────────

@main.route('/profile')
@login_required
def profile():
    return redirect(url_for('main.user_profile', username=current_user.username))


@main.route('/user/<username>')
@login_required
def user_profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    liked_pins = Pin.query.join(Like).filter(Like.user_id == user.id).order_by(Like.created_at.desc()).all()
    saved_pins = Pin.query.join(SavedPin).filter(SavedPin.user_id == user.id).order_by(SavedPin.created_at.desc()).all()
    boards = Board.query.filter_by(user_id=user.id).filter(
        (Board.is_private == False) | (Board.user_id == current_user.id)
    ).all()
    return render_template('profile.html',
        active_page='profile',
        user=user,
        liked_pins=liked_pins,
        saved_pins=saved_pins,
        boards=boards,
        is_own_profile=(user.id == current_user.id),
    )


@main.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(obj=current_user)
    if form.validate_on_submit():
        if form.username.data != current_user.username:
            if User.query.filter_by(username=form.username.data).first():
                flash('Username already taken.', 'danger')
                return render_template('edit_profile.html', active_page='profile', form=form)
        current_user.username = form.username.data
        current_user.bio = form.bio.data
        current_user.website = form.website.data or None
        if form.avatar.data:
            img = form.avatar.data
            ext = secure_filename(img.filename).rsplit('.', 1)[-1].lower()
            filename = f"avatar_{current_user.id}_{uuid.uuid4().hex[:8]}.{ext}"
            folder = current_app.config['UPLOAD_FOLDER']
            if current_user.avatar_filename and current_user.avatar_filename != 'default.jpg':
                old = os.path.join(folder, current_user.avatar_filename)
                if os.path.exists(old):
                    os.remove(old)
            compress_and_save_image(img, filename, folder, max_size=(400, 400))
            current_user.avatar_filename = filename
        db.session.commit()
        flash('Profile updated!', 'success')
        return redirect(url_for('main.profile'))
    return render_template('edit_profile.html', active_page='profile', form=form)


# ─── Settings ────────────────────────────────────────────────────────────────

@main.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    form = SettingsForm(obj=current_user)
    if form.validate_on_submit():
        if form.username.data != current_user.username:
            if User.query.filter_by(username=form.username.data).first():
                flash('Username already taken.', 'danger')
                return render_template('settings.html', active_page='settings', form=form)
        if form.email.data != current_user.email:
            if User.query.filter_by(email=form.email.data).first():
                flash('Email already in use.', 'danger')
                return render_template('settings.html', active_page='settings', form=form)
        if form.new_password.data:
            if not form.current_password.data or not current_user.check_password(form.current_password.data):
                flash('Current password is incorrect.', 'danger')
                return render_template('settings.html', active_page='settings', form=form)
            current_user.set_password(form.new_password.data)
            flash('Password changed successfully.', 'success')
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Settings saved!', 'success')
        return redirect(url_for('main.settings'))
    return render_template('settings.html', active_page='settings', form=form)


# ─── Follow ──────────────────────────────────────────────────────────────────

@main.route('/user/<username>/follow', methods=['POST'])
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({'ok': False, 'error': 'User not found'}), 404
    if user == current_user:
        return jsonify({'ok': False, 'error': 'Cannot follow yourself'}), 400
    if current_user.is_following(user):
        current_user.unfollow(user)
        following = False
    else:
        current_user.follow(user)
        following = True
        db.session.add(Notification(
            user_id=user.id, actor_id=current_user.id, type='follow'
        ))
    db.session.commit()
    return jsonify({'ok': True, 'following': following, 'followers_count': user.followers.count()})


# ─── Notifications ───────────────────────────────────────────────────────────

@main.route('/notifications')
@login_required
def notifications():
    try:
        notifs = Notification.query.filter_by(user_id=current_user.id)\
            .order_by(Notification.created_at.desc()).limit(50).all()
        Notification.query.filter_by(user_id=current_user.id, is_read=False).update({'is_read': True})
        db.session.commit()
    except Exception:
        db.session.rollback()
        notifs = []
    return render_template('notifications.html', active_page='notifications', notifications=notifs)


@main.route('/api/badge-counts')
@login_required
def api_badge_counts():
    try:
        msgs = current_user.unread_message_count()
        notifs = current_user.unread_notification_count()
    except Exception:
        msgs, notifs = 0, 0
    return jsonify({'messages': msgs, 'notifications': notifs})
