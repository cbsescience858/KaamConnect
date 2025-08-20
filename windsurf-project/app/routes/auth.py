from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from app.models.user import User, UserSkill
from app import db
from sqlalchemy import func
import re

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Generic registration (email-based). On success, log in and redirect to dashboard."""
    if request.method == 'POST':
        data = request.form
        username = (data.get('username') or '').strip()
        email = (data.get('email') or '').strip().lower()
        password = data.get('password')
        phone = (data.get('phone_number') or '').strip()
        user_type = (data.get('user_type') or 'client').strip()
        preferred_language = (
            (data.get('preferred_language') or '').strip()
            or session.get('preferred_language')
            or 'en'
        )

        if not username or not email or not password:
            flash('Please fill all required fields.', 'error')
            return render_template('auth/register.html'), 400

        # Ensure email uniqueness (case-insensitive) and username uniqueness
        if User.query.filter(func.lower(User.email) == email).first():
            flash('Email already exists.', 'error')
            return render_template('auth/register.html'), 400
        if User.query.filter_by(username=username).first():
            flash('Username already taken.', 'error')
            return render_template('auth/register.html'), 400

        user = User(
            username=username,
            email=email,
            phone_number=phone,
            user_type=user_type,
            preferred_language=preferred_language
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash('Registration successful!', 'success')
        return redirect(url_for('main.dashboard'))

    return render_template('auth/register.html')

@auth_bp.route('/register/client', methods=['GET', 'POST'])
def register_client():
    """Client registration. On success, auto-login and redirect to dashboard."""
    if request.method == 'POST':
        data = request.form
        username = (data.get('username') or '').strip()
        email = (data.get('email') or '').strip().lower()
        password = data.get('password')
        phone = (data.get('phone_number') or '').strip()
        preferred_language = session.get('preferred_language') or 'en'

        if not username or not email or not password:
            flash('Please fill all required fields.', 'error')
            return render_template('auth/register_client.html'), 400

        if User.query.filter(func.lower(User.email) == email).first():
            flash('Email already exists.', 'error')
            return render_template('auth/register_client.html'), 400
        if User.query.filter_by(username=username).first():
            flash('Username already taken.', 'error')
            return render_template('auth/register_client.html'), 400

        user = User(
            username=username,
            email=email,
            phone_number=phone,
            user_type='client',
            preferred_language=preferred_language
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash('Registration successful!', 'success')
        return redirect(url_for('main.dashboard'))

    return render_template('auth/register_client.html')

@auth_bp.route('/register/worker', methods=['GET', 'POST'])
def register_worker():
    """Worker registration (phone-first). Email is auto-generated if not supplied due to DB constraints.
    On success, auto-login and redirect to dashboard.
    """
    if request.method == 'POST':
        data = request.form
        username = (data.get('username') or '').strip()
        phone = (data.get('phone_number') or '').strip()
        password = data.get('password')
        state = (data.get('state') or '').strip()
        district = (data.get('district') or '').strip()
        city = (data.get('city') or '').strip()
        work_tags = (data.get('work_tags') or '').strip()
        # Optional email; if missing, synthesize one from phone
        email_input = (data.get('email') or '').strip().lower()
        preferred_language = session.get('preferred_language') or 'en'

        if not username or not phone or not password or not state or not district or not work_tags:
            flash('Please fill all required fields.', 'error')
            return render_template('auth/register_worker.html'), 400

        # Ensure username uniqueness
        if User.query.filter_by(username=username).first():
            flash('Username already taken.', 'error')
            return render_template('auth/register_worker.html'), 400

        # Normalize phone to digits for email synthesis
        digits = re.sub(r'\D+', '', phone)
        email = email_input or f"worker_{digits or 'user'}@users.local"

        # Ensure email uniqueness (case-insensitive); adjust if collision
        base_email = email
        suffix = 1
        while User.query.filter(func.lower(User.email) == email.lower()).first():
            email = base_email.replace('@', f"+{suffix}@")
            suffix += 1

        user = User(
            username=username,
            email=email.lower(),
            phone_number=phone,
            user_type='worker',
            preferred_language=preferred_language
        )
        user.set_password(password)
        db.session.add(user)
        db.session.flush()  # Get user.id before creating skills
        
        # Create user skills from work_tags
        if work_tags:
            tags = [tag.strip() for tag in work_tags.split(',') if tag.strip()]
            for tag in tags:
                skill = UserSkill(
                    user_id=user.id,
                    skill=tag,
                    experience_years=0  # Default to 0, can be updated later
                )
                db.session.add(skill)
        
        db.session.commit()
        login_user(user)
        flash('Registration successful!', 'success')
        return redirect(url_for('main.dashboard'))

    return render_template('auth/register_worker.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.form
        identifier_raw = (data.get('email') or '').strip()
        password = data.get('password')

        user = None
        if identifier_raw:
            if '@' in identifier_raw:
                # Treat as email (case-insensitive)
                identifier = identifier_raw.lower()
                user = User.query.filter(func.lower(User.email) == identifier).first()
            else:
                # Treat as phone; normalize to digits and compare against normalized stored phone numbers
                def normalize(p: str | None) -> str:
                    return re.sub(r'\D+', '', p or '')

                norm_id = normalize(identifier_raw)
                if norm_id:
                    candidates = User.query.filter(User.phone_number.isnot(None)).all()
                    for u in candidates:
                        if normalize(u.phone_number) == norm_id:
                            user = u
                            break

        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('main.dashboard'))
        else:
            flash('Invalid email/phone or password.', 'error')
            return redirect(url_for('auth.login'))
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('main.index'))
