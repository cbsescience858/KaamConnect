from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.models.user import User
from app.models import Job, JobApplication
from app import db
from datetime import datetime
from sqlalchemy import or_, and_

jobs_bp = Blueprint('jobs', __name__)

@jobs_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_job():
    if request.method == 'POST':
        data = request.form
        title = data.get('title')
        description = data.get('description')
        budget = data.get('budget')
        location = data.get('location')
        if not title or not description or not budget:
            flash('Please fill in all required fields.', 'error')
            return render_template('jobs/create.html')
        try:
            budget = float(budget)
        except ValueError:
            flash('Invalid budget amount.', 'error')
            return render_template('jobs/create.html')
        # Create new job
        new_job = Job(
            title=title,
            description=description,
            budget=budget,
            location=location,
            user_id=current_user.id
        )
        db.session.add(new_job)
        db.session.commit()
        flash('Job created successfully!', 'success')
        return redirect(url_for('jobs.view_job', job_id=new_job.id))
    return render_template('jobs/create.html')

@jobs_bp.route('/<int:job_id>')
@login_required
def view_job(job_id):
    job = Job.query.get_or_404(job_id)
    applications = JobApplication.query.filter_by(job_id=job_id).all()
    return render_template('jobs/view.html', job=job, applications=applications)

@jobs_bp.route('/apply/<int:job_id>', methods=['POST'])
@login_required
def apply_to_job(job_id):
    job = Job.query.get_or_404(job_id)
    
    # Check if user has already applied
    existing_application = JobApplication.query.filter_by(
        job_id=job_id,
        user_id=current_user.id
    ).first()
    
    if existing_application:
        flash('You have already applied to this job.', 'error')
        return redirect(url_for('jobs.view_job', job_id=job_id))
    
    # Create new application
    application = JobApplication(
        job_id=job_id,
        user_id=current_user.id,
        offer_amount=float(request.form.get('offer_amount')) if request.form.get('offer_amount') else None,
        message=request.form.get('message')
    )
    
    db.session.add(application)
    db.session.commit()
    
    flash('Application submitted successfully!', 'success')
    return redirect(url_for('jobs.view_job', job_id=job_id))

@jobs_bp.route('/search')
@login_required
def search_jobs():
    query = request.args.get('query', '')
    location = request.args.get('location', '')

    # Build base query
    jobs = Job.query.filter(Job.status == 'open')

    # Apply filters
    if query:
        jobs = jobs.filter(
            or_(
                Job.title.ilike(f'%{query}%'),
                Job.description.ilike(f'%{query}%')
            )
        )

    if location:
        jobs = jobs.filter(Job.location.ilike(f'%{location}%'))

    jobs = jobs.order_by(Job.created_at.desc())

    return render_template('jobs/search.html', jobs=jobs.all())

@jobs_bp.route('/matches')
@login_required
def job_matches():
    # Basic fallback matching: show recent open jobs
    jobs = Job.query.filter(Job.status == 'open').order_by(Job.created_at.desc()).all()
    return render_template('jobs/matches.html', jobs=jobs)

@jobs_bp.route('/<int:job_id>/applications')
@login_required
def job_applications(job_id):
    job = Job.query.get_or_404(job_id)
    
    # Only allow job creator to view applications
    if job.user_id != current_user.id:
        flash('You do not have permission to view these applications.', 'error')
        return redirect(url_for('main.dashboard'))
    
    applications = JobApplication.query.filter_by(job_id=job_id).all()
    return render_template('jobs/applications.html', job=job, applications=applications)

@jobs_bp.route('/<int:job_id>/applications/<int:application_id>/status', methods=['POST'])
@login_required
def update_application_status(job_id, application_id):
    job = Job.query.get_or_404(job_id)
    application = JobApplication.query.get_or_404(application_id)
    
    # Only allow job creator to update status
    if job.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    status = request.form.get('status')
    if status not in ['pending', 'accepted', 'rejected']:
        return jsonify({'error': 'Invalid status'}), 400
    
    application.status = status
    db.session.commit()
    
    return jsonify({'success': True})

@jobs_bp.route('/<int:job_id>/status', methods=['POST'])
@login_required
def update_job_status(job_id):
    job = Job.query.get_or_404(job_id)
    
    # Only allow job creator to update status
    if job.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    status = request.form.get('status')
    if status not in ['open', 'in_progress', 'completed', 'cancelled']:
        return jsonify({'error': 'Invalid status'}), 400
    
    job.status = status
    job.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({'success': True})
