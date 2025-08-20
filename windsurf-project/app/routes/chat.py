from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app.models.user import User
from app.models import Message, Job, JobApplication
from app import socketio, db
from flask_socketio import join_room, leave_room
from datetime import datetime
import phonenumbers

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/<int:job_id>')
@login_required
def chat_room(job_id):
    job = Job.query.get_or_404(job_id)
    
    # Check if user is either the job creator or has applied to the job
    if job.user_id != current_user.id:
        application = JobApplication.query.filter_by(
            job_id=job_id,
            user_id=current_user.id
        ).first()
        if not application:
            flash('You do not have permission to access this chat.', 'error')
            return redirect(url_for('main.dashboard'))
    
    messages = Message.query.filter_by(job_id=job_id).order_by(Message.timestamp).all()
    return render_template('chat/room.html', job=job, messages=messages)

@chat_bp.route('/messages/<int:job_id>')
@login_required
def get_messages(job_id):
    job = Job.query.get_or_404(job_id)
    
    # Check permissions
    if job.user_id != current_user.id:
        application = JobApplication.query.filter_by(
            job_id=job_id,
            user_id=current_user.id
        ).first()
        if not application:
            return jsonify({'error': 'Unauthorized'}), 403
    
    messages = Message.query.filter_by(job_id=job_id).order_by(Message.timestamp).all()
    return jsonify([{
        'id': msg.id,
        'content': msg.content,
        'timestamp': msg.timestamp.isoformat(),
        'user_id': msg.user_id,
        'language': msg.language
    } for msg in messages])

@socketio.on('send_message')
def handle_send_message(data):
    job_id = data.get('job_id')
    content = data.get('content')
    language = data.get('language', 'en')
    
    # Verify job exists
    job = Job.query.get(job_id)
    if not job:
        return
    
    # Verify user has permission to chat
    if job.user_id != current_user.id:
        application = JobApplication.query.filter_by(
            job_id=job_id,
            user_id=current_user.id
        ).first()
        if not application:
            return
    
    # Create message
    message = Message(
        job_id=job_id,
        user_id=current_user.id,
        content=content,
        language=language
    )
    
    db.session.add(message)
    db.session.commit()
    
    # Emit message to all connected clients
    socketio.emit('new_message', {
        'id': message.id,
        'content': message.content,
        'timestamp': message.timestamp.isoformat(),
        'user_id': message.user_id,
        'language': message.language
    }, room=f'job_{job_id}')

@socketio.on('join')
def on_join(data):
    job_id = data.get('job_id')
    
    # Verify job exists
    job = Job.query.get(job_id)
    if not job:
        return
    
    # Verify user has permission to join
    if job.user_id != current_user.id:
        application = JobApplication.query.filter_by(
            job_id=job_id,
            user_id=current_user.id
        ).first()
        if not application:
            return
    
    # Join room
    room = f'job_{job_id}'
    join_room(room)

@socketio.on('leave')
def on_leave(data):
    job_id = data.get('job_id')
    room = f'job_{job_id}'
    leave_room(room)

@chat_bp.route('/call/<int:job_id>')
@login_required
def initiate_call(job_id):
    job = Job.query.get_or_404(job_id)
    
    # Check if user is either the job creator or has applied to the job
    if job.user_id != current_user.id:
        application = JobApplication.query.filter_by(
            job_id=job_id,
            user_id=current_user.id
        ).first()
        if not application:
            flash('You do not have permission to initiate a call.', 'error')
            return redirect(url_for('main.dashboard'))
    
    # Get other party's phone number
    other_party = None
    if job.user_id == current_user.id:
        # Get applicant's phone number
        application = JobApplication.query.filter_by(
            job_id=job_id,
            status='accepted'
        ).first()
        if application:
            other_party = application.applicant
    else:
        # Get job creator's phone number
        other_party = job.creator
    
    if not other_party or not other_party.phone_number:
        flash('Phone number not available for the other party.', 'error')
        return redirect(url_for('chat.chat_room', job_id=job_id))
    
    # Format phone number
    try:
        phone_number = phonenumbers.parse(other_party.phone_number, 'IN')
        if not phonenumbers.is_valid_number(phone_number):
            raise ValueError
        formatted_number = phonenumbers.format_number(phone_number, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
    except:
        flash('Invalid phone number format.', 'error')
        return redirect(url_for('chat.chat_room', job_id=job_id))
    
    return render_template('chat/call.html', job=job, phone_number=formatted_number)
