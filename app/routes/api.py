from flask import Blueprint, jsonify, request, url_for
from flask_login import login_required, current_user
from sqlalchemy import func, desc
from app import db
from app.models import Pin, User, Tag, Like, pin_tags

api = Blueprint('api', __name__)


@api.route('/api/pins')
@login_required
def api_pins():
    page = request.args.get('page', 1, type=int)
    q = request.args.get('q', '').strip()
    tag = request.args.get('tag', '').strip()
    feed = request.args.get('feed', 'all')

    query = Pin.query
    if feed == 'following':
        followed_ids = [u.id for u in current_user.followed.all()]
        if not followed_ids:
            return jsonify({"pins": [], "has_next": False, "page": 1})
        query = query.filter(Pin.user_id.in_(followed_ids))

    if tag:
        query = query.join(Pin.tags).filter(Tag.name == tag.lower())

    if q:
        query = query.outerjoin(Pin.tags).filter(
            Pin.title.ilike(f"%{q}%") |
            Pin.description.ilike(f"%{q}%") |
            Tag.name.ilike(f"%{q}%")
        ).distinct()

    pins = query.order_by(Pin.created_at.desc()).paginate(page=page, per_page=20)
    user_liked_ids = {like.pin_id for like in current_user.likes}
    user_saved_ids = {save.pin_id for save in current_user.saves}

    items = []
    for p in pins.items:
        items.append({
            "id": p.id,
            "title": p.title,
            "description": p.description,
            "author": p.author.username,
            "author_id": p.author.id,
            "author_avatar": p.author.avatar_filename,
            "created_at": p.created_at.strftime("%Y-%m-%d"),
            "image_url": url_for("static", filename="uploads/" + p.image_filename),
            "likes_count": len(p.likes),
            "liked": p.id in user_liked_ids,
            "saved": p.id in user_saved_ids,
            "tags": [t.name for t in p.tags.all()],
            "views": p.views or 0,
        })
    return jsonify({"pins": items, "has_next": pins.has_next, "page": pins.page})


@api.route('/api/search_users')
@login_required
def search_users():
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify({"results": []})
    users = User.query.filter(User.username.ilike(f"%{q}%")).limit(10).all()
    return jsonify({
        "results": [
            {"id": u.id, "username": u.username, "avatar": u.avatar_filename}
            for u in users if u.id != current_user.id
        ]
    })


@api.route('/api/tags/popular')
@login_required
def api_popular_tags():
    tags = db.session.query(Tag.name, func.count(pin_tags.c.pin_id).label("cnt"))\
        .join(pin_tags, Tag.id == pin_tags.c.tag_id)\
        .group_by(Tag.id)\
        .order_by(desc("cnt"))\
        .limit(30).all()
    return jsonify({"tags": [{"name": t.name, "count": t.cnt} for t in tags]})
