from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.services.location import location_service
from app.models.user import User
from app.models import Job
from app import db
import phonenumbers
from phonenumbers.phonenumberutil import NumberParseException
from functools import wraps
import logging
import requests
import json
from pathlib import Path
from app.services.district_list import get_districts as get_districts_service

location_bp = Blueprint('location', __name__)
logger = logging.getLogger(__name__)

# Lightweight local fallback for districts when upstream is unavailable.
# Names must match the visible state names used in `_state_dropdown.html`.
LOCAL_DISTRICTS = {
    "Maharashtra": [
        "Mumbai", "Mumbai Suburban", "Pune", "Nagpur", "Thane", "Nashik", "Aurangabad", "Kolhapur"
    ],
    "Karnataka": [
        "Bengaluru Urban", "Bengaluru Rural", "Mysuru", "Mangaluru", "Belagavi", "Hubballi-Dharwad"
    ],
    "Delhi": [
        "New Delhi", "South Delhi", "North Delhi", "West Delhi", "East Delhi"
    ],
    "Uttar Pradesh": [
        "Lucknow", "Kanpur", "Varanasi", "Prayagraj", "Ghaziabad", "Noida", "Agra"
    ],
    "Tamil Nadu": [
        "Chennai", "Coimbatore", "Madurai", "Tiruchirappalli", "Salem"
    ],
    "Gujarat": [
        "Ahmedabad", "Surat", "Vadodara", "Rajkot", "Bhavnagar"
    ],
    "West Bengal": [
        "Kolkata", "Howrah", "Darjeeling", "Siliguri"
    ],
    "Rajasthan": [
        "Jaipur", "Jodhpur", "Udaipur", "Kota"
    ],
    "Bihar": [
        "Patna", "Gaya", "Bhagalpur"
    ],
    "Telangana": [
        "Hyderabad", "Warangal", "Nalgonda"
    ],
    "Kerala": [
        "Thiruvananthapuram", "Kochi", "Kozhikode"
    ],
    "Madhya Pradesh": [
        "Bhopal", "Indore", "Jabalpur", "Gwalior"
    ],
    "Andhra Pradesh": [
        "Visakhapatnam", "Vijayawada", "Guntur"
    ],
    "Punjab": [
        "Amritsar", "Ludhiana", "Jalandhar"
    ],
    "Haryana": [
        "Gurugram", "Faridabad", "Panipat"
    ],
}

def validate_phone_number(phone_number: str) -> bool:
    """Validate phone number format"""
    try:
        parsed = phonenumbers.parse(phone_number, None)
        return phonenumbers.is_valid_number(parsed)
    except NumberParseException:
        return False

def format_phone_number(phone_number: str) -> str:
    """Format phone number to E.164 standard"""
    try:
        parsed = phonenumbers.parse(phone_number, 'IN')  # Default to India
        return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
    except NumberParseException:
        return phone_number

@location_bp.route('/update', methods=['POST'])
@login_required
def update_location():
    """Update user's current location"""
    data = request.get_json()
    
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    address = data.get('address')
    
    if not all([latitude, longitude]):
        return jsonify({'error': 'Latitude and longitude are required'}), 400
    
    try:
        # Update user's location
        current_user.latitude = float(latitude)
        current_user.longitude = float(longitude)
        
        # If address is not provided, try to get it from coordinates
        if not address:
            location_data = location_service.get_address(latitude, longitude)
            if location_data:
                address = location_data.get('display_name', '')
        
        if address:
            current_user.location = address
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Location updated successfully',
            'location': {
                'latitude': current_user.latitude,
                'longitude': current_user.longitude,
                'address': current_user.location
            }
        })
    except Exception as e:
        logger.error(f"Error updating location: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to update location'}), 500

@location_bp.route('/nearby-jobs')
@login_required
def get_nearby_jobs():
    """Get jobs near user's current location"""
    # Get user's current location
    if not all([current_user.latitude, current_user.longitude]):
        return jsonify({'error': 'User location not available'}), 400
    
    try:
        radius = float(request.args.get('radius', 10))  # Default 10km radius
        limit = int(request.args.get('limit', 20))  # Default 20 results
        
        nearby_jobs = location_service.get_nearby_jobs(
            current_user.latitude,
            current_user.longitude,
            radius_km=radius,
            limit=limit
        )
        
        return jsonify({
            'success': True,
            'jobs': nearby_jobs,
            'current_location': {
                'latitude': current_user.latitude,
                'longitude': current_user.longitude,
                'address': current_user.location
            },
            'search_radius_km': radius
        })
    except Exception as e:
        logger.error(f"Error getting nearby jobs: {str(e)}")
        return jsonify({'error': 'Failed to get nearby jobs'}), 500

@location_bp.route('/initiate-call', methods=['POST'])
@login_required
def initiate_call():
    """Initiate a phone call between users"""
    data = request.get_json()
    
    job_id = data.get('job_id')
    recipient_id = data.get('recipient_id')
    
    if not job_id or not recipient_id:
        return jsonify({'error': 'Job ID and recipient ID are required'}), 400
    
    # Verify job exists and user has permission
    job = Job.query.get_or_404(job_id)
    if job.creator_id != current_user.id and job.creator_id != recipient_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get recipient's phone number
    recipient = User.query.get_or_404(recipient_id)
    if not recipient.phone_number:
        return jsonify({'error': 'Recipient does not have a phone number'}), 400
    
    # Format phone numbers
    caller_number = format_phone_number(current_user.phone_number or '')
    recipient_number = format_phone_number(recipient.phone_number)
    
    # In a real implementation, you would integrate with a telephony service here
    # For example: Twilio, Plivo, or any other VoIP service
    
    try:
        # Log the call (you would implement this in your database)
        # call = CallLog(
        #     caller_id=current_user.id,
        #     recipient_id=recipient_id,
        #     job_id=job_id,
        #     status='initiated'
        # )
        # db.session.add(call)
        # db.session.commit()
        
        # Return success with call details
        return jsonify({
            'success': True,
            'message': 'Call initiated',
            'call': {
                'caller_id': current_user.id,
                'recipient_id': recipient_id,
                'recipient_number': recipient_number,  # In production, mask or omit sensitive data
                'job_id': job_id,
                'status': 'initiated',
                'call_sid': 'mock_call_sid_12345'  # Replace with actual call SID from telephony service
            }
        })
        
    except Exception as e:
        logger.error(f"Error initiating call: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to initiate call'}), 500

@location_bp.route('/call-status', methods=['POST'])
@login_required
def call_status():
    """Webhook for call status updates from telephony service"""
    # This would be called by your telephony service (e.g., Twilio webhook)
    call_sid = request.form.get('CallSid')
    call_status = request.form.get('CallStatus')
    
    if not all([call_sid, call_status]):
        return jsonify({'error': 'Missing parameters'}), 400
    
    try:
        # Update call log in database
        # call = CallLog.query.filter_by(call_sid=call_sid).first()
        # if call:
        #     call.status = call_status
        #     if call_status in ['completed', 'busy', 'failed', 'no-answer']:
        #         call.ended_at = datetime.utcnow()
        #     db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error updating call status: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to update call status'}), 500

@location_bp.route('/call-history')
@login_required
def call_history():
    """Get user's call history"""
    try:
        # Get call history from database
        # calls = CallLog.query.filter(
        #     (CallLog.caller_id == current_user.id) | 
        #     (CallLog.recipient_id == current_user.id)
        # ).order_by(CallLog.created_at.desc()).limit(50).all()
        
        # return jsonify({
        #     'success': True,
        #     'calls': [{
        #         'id': call.id,
        #         'caller_id': call.caller_id,
        #         'recipient_id': call.recipient_id,
        #         'job_id': call.job_id,
        #         'status': call.status,
        #         'created_at': call.created_at.isoformat(),
        #         'ended_at': call.ended_at.isoformat() if call.ended_at else None
        #     } for call in calls]
        # })
        
        # Mock response until database model is implemented
        return jsonify({
            'success': True,
            'calls': []
        })
        
    except Exception as e:
        logger.error(f"Error getting call history: {str(e)}")
        return jsonify({'error': 'Failed to get call history'}), 500


@location_bp.route('/districts', methods=['GET'])
def get_districts_by_state():
    """Proxy the government endpoint to fetch districts for a given state.
    Query param: state (string) - must match the visible state name used in `_state_dropdown.html`.
    Returns: { districts: ["District 1", "District 2", ...] }
    """
    state = request.args.get('state', '').strip()
    if not state:
        # Return 200 with empty list so UI shows a friendly message
        return jsonify({'districts': []})

    try:
        districts = get_districts_service(state)
        return jsonify({'districts': districts})
    except Exception as e:
        logger.error(f"Error getting districts for state '{state}': {e}")
        return jsonify({'districts': []})
