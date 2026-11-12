import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory, jsonify, abort
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from config import Config
from models import db, User, Item, Claim, Conversation, Message
from forms import RegisterForm, LoginForm, ItemForm, ResetRequestForm, ResetPasswordForm, ClaimForm, ChatMessageForm
from notify import send_email, send_sms
from utils import generate_token, confirm_token, find_matches_for_item

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def current_user():
    uid = session.get('user_id')
    if not uid:
        return None
    return User.query.get(uid)

@app.route('/')
def index():
    q = request.args.get('q', '')
    category = request.args.get('category', '')
    location = request.args.get('location', '')
    item_type = request.args.get('type', '')
    items = Item.query.filter(Item.status != 'removed')
    if q:
        items = items.filter((Item.title.ilike(f"%{q}%")) | (Item.description.ilike(f"%{q}%")))
    if category:
        items = items.filter_by(category=category)
    if location:
        items = items.filter(Item.location.ilike(f"%{location}%"))
    if item_type:
        items = items.filter_by(item_type=item_type)
    items = items.order_by(Item.date_reported.desc()).all()
    # Stats for hero section
    total_items = Item.query.filter(Item.status != 'removed').count()
    resolved = Item.query.filter_by(status='claimed').count()
    total_users = User.query.count()
    stats = {'total': total_items, 'resolved': resolved, 'users': total_users}
    return render_template('index.html', items=items, user=current_user(), stats=stats)

@app.route('/register', methods=['GET','POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            flash('Email already registered', 'warning')
            return redirect(url_for('register'))
        user = User(name=form.name.data, email=form.email.data, phone=form.phone.data, password_hash=generate_password_hash(form.password.data))
        db.session.add(user)
        db.session.commit()
        flash('Registered — please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form, user=current_user())

@app.route('/login', methods=['GET','POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        u = User.query.filter_by(email=form.email.data).first()
        if u and check_password_hash(u.password_hash, form.password.data):
            session['user_id'] = u.id
            flash('Logged in', 'success')
            return redirect(url_for('index'))
        flash('Invalid credentials', 'danger')
    return render_template('login.html', form=form, user=current_user())

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Logged out', 'info')
    return redirect(url_for('index'))

@app.route('/reset-request', methods=['GET','POST'])
def reset_request():
    form = ResetRequestForm()
    if form.validate_on_submit():
        u = User.query.filter_by(email=form.email.data).first()
        if u:
            token = generate_token(u.email)
            link = url_for('reset_token', token=token, _external=True)
            send_email(u.email, "Password reset", f"Use this link to reset your password:\n\n{link}")
            flash('Password reset link sent (check console if no SMTP configured).', 'info')
        else:
            flash('If account exists, a reset link will be sent.', 'info')
        return redirect(url_for('login'))
    return render_template('reset_request.html', form=form, user=current_user())

@app.route('/reset/<token>', methods=['GET','POST'])
def reset_token(token):
    email = confirm_token(token)
    if not email:
        flash('Invalid or expired token.', 'danger')
        return redirect(url_for('reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=email).first()
        if user:
            user.password_hash = generate_password_hash(form.password.data)
            db.session.commit()
            flash('Password updated — please log in.', 'success')
            return redirect(url_for('login'))
        flash('User not found.', 'danger')
    return render_template('reset_token.html', form=form, user=current_user())

@app.route('/report/missing', methods=['GET','POST'])
def report_missing():
    form = ItemForm()
    if form.validate_on_submit():
        filename = None
        f = request.files.get('image')
        if f and f.filename and allowed_file(f.filename):
            filename = secure_filename(f.filename)
            path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            base, ext = os.path.splitext(filename)
            i = 1
            while os.path.exists(path):
                filename = f"{base}_{i}{ext}"
                path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                i += 1
            f.save(path)
        item = Item(
            title=form.title.data,
            description=form.description.data,
            category=form.category.data,
            location=form.location.data,
            date_lost_found=form.date_lost_found.data,
            item_type='missing',
            image_filename=filename,
            contact_details=form.contact_details.data,
            user_id=session.get('user_id')
        )
        db.session.add(item)
        db.session.commit()
        matches = find_matches_for_item(db, item, threshold=0.45)
        if matches:
            flash(f'Potential matches found: {len(matches)} — check the item page.', 'info')
        else:
            flash('Missing item reported.', 'success')
        return redirect(url_for('item_detail', item_id=item.id))
    return render_template('report_missing.html', form=form, user=current_user())

@app.route('/report/found', methods=['GET','POST'])
def report_found():
    form = ItemForm()
    if form.validate_on_submit():
        filename = None
        f = request.files.get('image')
        if f and f.filename and allowed_file(f.filename):
            filename = secure_filename(f.filename)
            path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            base, ext = os.path.splitext(filename)
            i = 1
            while os.path.exists(path):
                filename = f"{base}_{i}{ext}"
                path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                i += 1
            f.save(path)
        item = Item(
            title=form.title.data,
            description=form.description.data,
            category=form.category.data,
            location=form.location.data,
            date_lost_found=form.date_lost_found.data,
            item_type='found',
            image_filename=filename,
            contact_details=form.contact_details.data,
            user_id=session.get('user_id')
        )
        db.session.add(item)
        db.session.commit()
        matches = find_matches_for_item(db, item, threshold=0.45)
        if matches:
            flash(f'Potential matches found: {len(matches)} — check the item page.', 'info')
        else:
            flash('Found item reported.', 'success')
        return redirect(url_for('item_detail', item_id=item.id))
    return render_template('report_found.html', form=form, user=current_user())

@app.route('/item/<int:item_id>', methods=['GET','POST'])
def item_detail(item_id):
    it = Item.query.get_or_404(item_id)
    matches = find_matches_for_item(db, it, threshold=0.4)
    claim_form = ClaimForm()
    if claim_form.validate_on_submit():
        if not current_user():
            flash('Please login to make a claim.', 'warning')
            return redirect(url_for('login'))
        claim = Claim(item_id=it.id, claimant_id=current_user().id, message=claim_form.message.data, proof=claim_form.proof.data)
        db.session.add(claim)
        db.session.commit()
        if it.user_id:
            conv = Conversation(claim_id=claim.id, reporter_id=it.user_id, claimant_id=current_user().id)
            db.session.add(conv)
            db.session.commit()
            owner = User.query.get(it.user_id)
            subject = "New claim submitted for your item"
            body = f"A user has submitted a claim for your item '{it.title}'. Visit: {url_for('item_detail', item_id=it.id, _external=True)}"
            if owner and owner.email:
                send_email(owner.email, subject, body)
            if owner and owner.phone:
                send_sms(owner.phone, f"New claim for '{it.title}'.")
        flash('Claim submitted — admin will review and you can chat with the reporter.', 'info')
        return redirect(url_for('item_detail', item_id=item_id))
    return render_template('item.html', item=it, matches=matches, claim_form=claim_form, user=current_user())

@app.route('/dashboard')
def dashboard():
    user = current_user()
    if not user:
        flash('Please login to access your dashboard.', 'warning')
        return redirect(url_for('login'))
    items = Item.query.filter_by(user_id=user.id).order_by(Item.date_reported.desc()).all()
    claims = Claim.query.filter_by(claimant_id=user.id).order_by(Claim.created_at.desc()).all()
    # Get conversations for this user
    convs = Conversation.query.filter(
        (Conversation.reporter_id == user.id) | (Conversation.claimant_id == user.id)
    ).order_by(Conversation.created_at.desc()).all()
    # Stats
    active_count = sum(1 for i in items if i.status == 'active')
    claimed_count = sum(1 for i in items if i.status == 'claimed')
    return render_template('dashboard.html', user=user, items=items, claims=claims,
                           conversations=convs, active_count=active_count, claimed_count=claimed_count)

@app.route('/profile', methods=['GET','POST'])
def profile():
    user = current_user()
    if not user:
        flash('Please login to view your profile.', 'warning')
        return redirect(url_for('login'))
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        if name:
            user.name = name
        user.phone = phone
        # Handle password change
        new_pass = request.form.get('new_password', '').strip()
        if new_pass and len(new_pass) >= 6:
            user.password_hash = generate_password_hash(new_pass)
            flash('Password updated.', 'success')
        elif new_pass:
            flash('Password must be at least 6 characters.', 'warning')
        db.session.commit()
        flash('Profile updated.', 'success')
        return redirect(url_for('profile'))
    item_count = Item.query.filter_by(user_id=user.id).count()
    claim_count = Claim.query.filter_by(claimant_id=user.id).count()
    return render_template('profile.html', user=user, item_count=item_count, claim_count=claim_count)

@app.route('/delete-item/<int:item_id>', methods=['POST'])
def delete_item(item_id):
    user = current_user()
    if not user:
        abort(403)
    it = Item.query.get_or_404(item_id)
    if it.user_id != user.id and not user.is_admin:
        abort(403)
    it.status = 'removed'
    db.session.commit()
    flash('Item removed.', 'success')
    return redirect(url_for('dashboard'))

@app.route('/chat/<int:conv_id>')
def chat_page(conv_id):
    conv = Conversation.query.get_or_404(conv_id)
    u = current_user()
    if not u or (u.id not in [conv.reporter_id, conv.claimant_id]):
        flash('Access denied to this conversation.', 'danger')
        return redirect(url_for('index'))
    form = ChatMessageForm()
    return render_template('chat.html', conv=conv, form=form, user=u)

@app.route('/api/chat/<int:conv_id>/messages')
def chat_messages(conv_id):
    conv = Conversation.query.get_or_404(conv_id)
    u = current_user()
    if not u or (u.id not in [conv.reporter_id, conv.claimant_id]):
        return jsonify({'error':'access denied'}), 403
    since = request.args.get('since')
    q = Message.query.filter_by(conversation_id=conv.id).order_by(Message.created_at.asc())
    if since:
        try:
            dt = datetime.fromisoformat(since)
            q = q.filter(Message.created_at > dt)
        except Exception:
            pass
    msgs = [{'id': m.id, 'sender_id': m.sender_id, 'sender_name': m.sender.name if m.sender else 'User', 'body': m.body, 'created_at': m.created_at.isoformat()} for m in q.all()]
    return jsonify({'messages': msgs})

@app.route('/api/chat/<int:conv_id>/send', methods=['POST'])
def chat_send(conv_id):
    conv = Conversation.query.get_or_404(conv_id)
    u = current_user()
    if not u or (u.id not in [conv.reporter_id, conv.claimant_id]):
        return jsonify({'error':'access denied'}), 403
    data = request.get_json() or {}
    body = data.get('body','').strip()
    if not body:
        return jsonify({'error':'empty message'}), 400
    m = Message(conversation_id=conv.id, sender_id=u.id, body=body)
    db.session.add(m)
    db.session.commit()
    other_id = conv.claimant_id if u.id == conv.reporter_id else conv.reporter_id
    other = User.query.get(other_id)
    if other:
        subject = f"New message about item conversation #{conv.id}"
        body_text = f"New message from {u.name}: {body}\n\nVisit: {url_for('chat_page', conv_id=conv.id, _external=True)}"
        if other.email:
            send_email(other.email, subject, body_text)
        if other.phone:
            send_sms(other.phone, f"New message from {u.name} about your item.")
    return jsonify({'ok': True, 'message': {'id': m.id, 'body': m.body, 'created_at': m.created_at.isoformat(), 'sender_id': m.sender_id, 'sender_name': u.name}})

@app.route('/api/stats')
def api_stats():
    total = Item.query.filter(Item.status != 'removed').count()
    resolved = Item.query.filter_by(status='claimed').count()
    active = Item.query.filter_by(status='active').count()
    users = User.query.count()
    return jsonify({'total': total, 'resolved': resolved, 'active': active, 'users': users})

@app.route('/claims')
def all_claims():
    user = current_user()
    if not user or not user.is_admin:
        flash('Admin access required', 'danger')
        return redirect(url_for('index'))
    claims = Claim.query.order_by(Claim.created_at.desc()).all()
    return render_template('claims.html', claims=claims, user=user)

@app.route('/claim/<int:claim_id>/action', methods=['POST'])
def claim_action(claim_id):
    user = current_user()
    if not user or not user.is_admin:
        abort(403)
    action = request.form.get('action')
    claim = Claim.query.get_or_404(claim_id)
    if action == 'approve':
        claim.status = 'approved'
        claim.item.status = 'claimed'
        if claim.item and claim.claimant:
            send_email(claim.claimant.email, "Your claim was approved", f"Your claim for '{claim.item.title}' was approved.")
            if claim.item.reporter and claim.item.reporter.email:
                send_email(claim.item.reporter.email, "Claim approved", f"Claim for '{claim.item.title}' approved — please coordinate via chat.")
    elif action == 'reject':
        claim.status = 'rejected'
    db.session.commit()
    flash('Claim updated.', 'success')
    return redirect(url_for('all_claims'))

@app.route('/admin')
def admin_panel():
    user = current_user()
    if not user or not user.is_admin:
        flash('Admin access required', 'danger')
        return redirect(url_for('index'))
    items = Item.query.order_by(Item.date_reported.desc()).all()
    users = User.query.order_by(User.created_at.desc()).all()
    claims = Claim.query.order_by(Claim.created_at.desc()).all()
    stats = {
        'total_items': Item.query.count(),
        'active_items': Item.query.filter_by(status='active').count(),
        'claimed_items': Item.query.filter_by(status='claimed').count(),
        'total_users': User.query.count(),
        'pending_claims': Claim.query.filter_by(status='pending').count(),
    }
    return render_template('admin.html', items=items, users=users, claims=claims, user=user, stats=stats)

@app.route('/admin/item/<int:item_id>/verify', methods=['POST'])
def admin_verify_item(item_id):
    user = current_user()
    if not user or not user.is_admin:
        abort(403)
    it = Item.query.get_or_404(item_id)
    action = request.form.get('action')
    if action == 'approve':
        it.is_verified = True
        it.status = 'approved'
    elif action == 'remove':
        it.status = 'removed'
    db.session.commit()
    flash('Item updated.', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

def ensure_db_and_admin():
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(email='admin@college.edu').first():
            admin = User(name='Admin', email='admin@college.edu', password_hash=generate_password_hash('admin123'), is_admin=True)
            db.session.add(admin)
            db.session.commit()
ensure_db_and_admin()

if __name__ == '__main__':
    app.run(debug=True)
