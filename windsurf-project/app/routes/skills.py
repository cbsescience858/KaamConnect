from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.models.user import User
from app.models import Job
from app import db

skills_bp = Blueprint('skills', __name__)

@skills_bp.route('/user', methods=['GET'])
@login_required
def get_user_skills():
    """Get all skills for the current user"""
    user_skills = current_user.skills.all()
    return jsonify({
        'success': True,
        'skills': [{
            'id': skill.id,
            'skill': skill.skill,
            'experience_years': skill.experience_years
        } for skill in user_skills]
    })

@skills_bp.route('/user', methods=['POST'])
@login_required
def add_skill():
    """Add a new skill for the current user"""
    data = request.get_json()
    skill_name = data.get('skill')
    experience_years = data.get('experience_years', 0)
    
    if not skill_name:
        return jsonify({'error': 'Skill name is required'}), 400
    
    # Check if skill already exists for user
    existing_skill = UserSkill.query.filter_by(
        user_id=current_user.id,
        skill=skill_name.lower()
    ).first()
    
    if existing_skill:
        return jsonify({
            'error': 'You already have this skill in your profile',
            'skill': {
                'id': existing_skill.id,
                'skill': existing_skill.skill,
                'experience_years': existing_skill.experience_years
            }
        }), 400
    
    # Add new skill
    new_skill = UserSkill(
        user_id=current_user.id,
        skill=skill_name.lower(),
        experience_years=experience_years
    )
    
    db.session.add(new_skill)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Skill added successfully',
        'skill': {
            'id': new_skill.id,
            'skill': new_skill.skill,
            'experience_years': new_skill.experience_years
        }
    }), 201

@skills_bp.route('/user/<int:skill_id>', methods=['PUT'])
@login_required
def update_skill(skill_id):
    """Update an existing skill"""
    skill = UserSkill.query.get_or_404(skill_id)
    
    # Check if skill belongs to current user
    if skill.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    experience_years = data.get('experience_years')
    
    if experience_years is not None:
        skill.experience_years = experience_years
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Skill updated successfully',
        'skill': {
            'id': skill.id,
            'skill': skill.skill,
            'experience_years': skill.experience_years
        }
    })

@skills_bp.route('/user/<int:skill_id>', methods=['DELETE'])
@login_required
def delete_skill(skill_id):
    """Remove a skill from user's profile"""
    skill = UserSkill.query.get_or_404(skill_id)
    
    # Check if skill belongs to current user
    if skill.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    db.session.delete(skill)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Skill removed successfully'
    })

@skills_bp.route('/suggest')
@login_required
def suggest_skills():
    """Suggest skills based on user input"""
    query = request.args.get('q', '').lower()
    
    if not query or len(query) < 2:
        return jsonify({'suggestions': []})
    
    # Get popular skills that match the query
    popular_skills = db.session.query(
        JobTag.tag,
        db.func.count(JobTag.tag).label('count')
    ).filter(
        JobTag.tag.ilike(f'%{query}%')
    ).group_by(
        JobTag.tag
    ).order_by(
        db.desc('count')
    ).limit(10).all()
    
    # Get user's existing skills to avoid duplicates
    user_skills = {skill.skill.lower() for skill in current_user.skills.all()}
    
    suggestions = []
    for tag, count in popular_skills:
        if tag.lower() not in user_skills:
            suggestions.append({
                'skill': tag,
                'popularity': count
            })
    
    return jsonify({
        'suggestions': suggestions[:10]  # Limit to 10 suggestions
    })

@skills_bp.route('/top')
@login_required
def get_top_skills():
    """Get top skills in the platform"""
    top_skills = db.session.query(
        JobTag.tag,
        db.func.count(JobTag.tag).label('count')
    ).group_by(
        JobTag.tag
    ).order_by(
        db.desc('count')
    ).limit(20).all()
    
    return jsonify({
        'top_skills': [{
            'skill': tag,
            'count': count
        } for tag, count in top_skills]
    })
