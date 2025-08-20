from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.models.user import User
from app.models import Job, JobApplication
from app import db

payments_bp = Blueprint('payments', __name__)

@payments_bp.route('/<int:job_id>/offer')
@login_required
def view_offers(job_id):
    job = Job.query.get_or_404(job_id)
    
    # Check if user has permission to view offers
    if job.creator_id != current_user.id:
        flash('You do not have permission to view offers for this job.', 'error')
        return redirect(url_for('main.dashboard'))
    
    applications = JobApplication.query.filter_by(job_id=job_id).all()
    return render_template('payments/offers.html', job=job, applications=applications)

@payments_bp.route('/<int:job_id>/applications/<int:application_id>/make-offer', methods=['POST'])
@login_required
def make_offer(job_id, application_id):
    job = Job.query.get_or_404(job_id)
    application = JobApplication.query.get_or_404(application_id)
    
    # Check if user has permission to make offer
    if job.creator_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Check if application is still pending
    if application.status != 'pending':
        return jsonify({'error': 'Application is not in pending status'}), 400
    
    # Get offer amount
    offer_amount = float(request.form.get('offer_amount'))
    if offer_amount <= 0:
        return jsonify({'error': 'Invalid offer amount'}), 400
    
    # Update application with offer
    application.offer_amount = offer_amount
    application.status = 'offered'
    db.session.commit()
    
    return jsonify({'success': True})

@payments_bp.route('/<int:job_id>/applications/<int:application_id>/accept-offer', methods=['POST'])
@login_required
def accept_offer(job_id, application_id):
    job = Job.query.get_or_404(job_id)
    application = JobApplication.query.get_or_404(application_id)
    
    # Check if user has permission to accept offer
    if application.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Check if offer exists
    if not application.offer_amount:
        return jsonify({'error': 'No offer has been made for this application'}), 400
    
    # Accept offer
    application.status = 'accepted'
    job.status = 'in_progress'
    db.session.commit()
    
    return jsonify({'success': True})

@payments_bp.route('/<int:job_id>/applications/<int:application_id>/reject-offer', methods=['POST'])
@login_required
def reject_offer(job_id, application_id):
    job = Job.query.get_or_404(job_id)
    application = JobApplication.query.get_or_404(application_id)
    
    # Check if user has permission to reject offer
    if application.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Check if offer exists
    if not application.offer_amount:
        return jsonify({'error': 'No offer has been made for this application'}), 400
    
    # Reject offer
    application.status = 'rejected'
    application.offer_amount = None
    db.session.commit()
    
    return jsonify({'success': True})

@payments_bp.route('/<int:job_id>/complete', methods=['POST'])
@login_required
def complete_job(job_id):
    job = Job.query.get_or_404(job_id)
    
    # Check if user has permission to complete job
    if job.creator_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Check if job is in progress
    if job.status != 'in_progress':
        return jsonify({'error': 'Job is not in progress'}), 400
    
    # Get accepted application
    application = JobApplication.query.filter_by(
        job_id=job_id,
        status='accepted'
    ).first()
    
    if not application:
        return jsonify({'error': 'No accepted application found for this job'}), 400
    
    # Complete job
    job.status = 'completed'
    job.completed_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({'success': True})

@payments_bp.route('/<int:job_id>/cancel', methods=['POST'])
@login_required
def cancel_job(job_id):
    job = Job.query.get_or_404(job_id)
    
    # Check if user has permission to cancel job
    if job.creator_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Cancel job
    job.status = 'cancelled'
    job.cancelled_at = datetime.utcnow()
    
    # Reset all applications to cancelled
    applications = JobApplication.query.filter_by(job_id=job_id).all()
    for app in applications:
        app.status = 'cancelled'
    
    db.session.commit()
    
    return jsonify({'success': True})

@payments_bp.route('/<int:job_id>/applications/<int:application_id>/payment-status')
@login_required
def payment_status(job_id, application_id):
    job = Job.query.get_or_404(job_id)
    application = JobApplication.query.get_or_404(application_id)
    
    # Check if user has permission to view payment status
    if application.user_id != current_user.id and job.creator_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get payment status
    status = 'pending'
    if job.status == 'completed':
        status = 'completed'
    elif job.status == 'cancelled':
        status = 'cancelled'
    
    return jsonify({
        'status': status,
        'amount': application.offer_amount,
        'job_status': job.status
    })
