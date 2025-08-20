from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models.user import User, Job, JobApplication
from app import db, socketio

main = Blueprint('main', __name__)

@main.route('/')
def index():
    from flask_login import current_user
    from flask import redirect, url_for
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    else:
        return redirect(url_for('auth.login'))

@main.route('/dashboard')
@login_required
def dashboard():
    if current_user.user_type == 'client':
        return render_template('dashboard/client.html')
    else:
        return render_template('dashboard/worker.html')

@main.route('/jobs')
@login_required
def jobs():
    jobs = Job.query.filter_by(status='open').all()
    return render_template('jobs/list.html', jobs=jobs)

@main.route('/jobs/create', methods=['GET', 'POST'])
@login_required
def create_job():
    if request.method == 'POST':
        data = request.form
        
        new_job = Job(
            title=data.get('title'),
            description=data.get('description'),
            budget=float(data.get('budget')) if data.get('budget') else None,
            location=data.get('location'),
            user_id=current_user.id
        )
        
        db.session.add(new_job)
        db.session.commit()
        
        return redirect(url_for('main.jobs'))
    
    return render_template('jobs/create.html')

@main.route('/jobs/<int:job_id>')
@login_required
def job_detail(job_id):
    # Delegate to the jobs blueprint's canonical view route
    return redirect(url_for('jobs.view_job', job_id=job_id))

@main.route('/jobs/<int:job_id>/apply', methods=['POST'])
@login_required
def apply_to_job(job_id):
    job = Job.query.get_or_404(job_id)
    
    application = JobApplication(
        job_id=job_id,
        user_id=current_user.id,
        offer_amount=float(request.form.get('offer_amount')) if request.form.get('offer_amount') else None,
        message=request.form.get('message')
    )
    
    db.session.add(application)
    db.session.commit()
    
    # Notify the job creator
    socketio.emit('new_application', {
        'job_id': job_id,
        'applicant_id': current_user.id
    }, room=f'job_{job_id}')
    
    return jsonify({'status': 'success'})

@main.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

@main.route('/chat')
@login_required
def chat():
    # The chat room requires a specific job_id and is handled in `app/routes/chat.py`.
    # Avoid referencing a non-existent 'chat.html' by redirecting users to the jobs list.
    flash('Please open a chat from a specific job.', 'info')
    return redirect(url_for('main.jobs'))
