from flask import Blueprint, request, jsonify, redirect, url_for, flash, session
from flask_login import login_required, current_user
from app.services.translation import translation_service
from ..models import User, Message
from .. import db

language_bp = Blueprint('language', __name__)

@language_bp.route('/set', methods=['POST'])
def set_language():
    """Set preferred language.
    - If user is authenticated, persist to DB.
    - If not, save to session so UI updates immediately.
    Always redirect back to the referrer or home.
    """
    language_code = request.form.get('language')

    supported = translation_service.get_supported_languages()
    if language_code not in supported:
        flash('Unsupported language selected.', 'error')
        return redirect(request.referrer or url_for('main.index'))

    if current_user.is_authenticated:
        current_user.preferred_language = language_code
        db.session.commit()
    else:
        session['preferred_language'] = language_code

    flash('Language changed successfully!', 'success')
    return redirect(request.referrer or url_for('main.index'))

@language_bp.route('/translate', methods=['POST'])
@login_required
def translate_text():
    """Translate text from one language to another"""
    data = request.get_json()
    
    text = data.get('text')
    source_lang = data.get('source_lang')
    target_lang = data.get('target_lang')
    
    if not all([text, source_lang, target_lang]):
        return jsonify({'error': 'Missing required parameters'}), 400
    
    if source_lang not in translation_service.get_supported_languages():
        return jsonify({'error': 'Unsupported source language'}), 400
    
    if target_lang not in translation_service.get_supported_languages():
        return jsonify({'error': 'Unsupported target language'}), 400
    
    try:
        translated_text = translation_service.translate_text(text, source_lang, target_lang)
        return jsonify({
            'success': True,
            'original_text': text,
            'translated_text': translated_text,
            'source_lang': source_lang,
            'target_lang': target_lang
        })
    except Exception as e:
        return jsonify({'error': f'Translation failed: {str(e)}'}), 500

@language_bp.route('/detect', methods=['POST'])
@login_required
def detect_language():
    """Detect the language of given text"""
    data = request.get_json()
    text = data.get('text')
    
    if not text:
        return jsonify({'error': 'Text is required'}), 400
    
    try:
        detected_lang = translation_service.detect_language(text)
        return jsonify({
            'success': True,
            'text': text,
            'detected_language': detected_lang,
            'language_name': translation_service.get_supported_languages().get(detected_lang, 'Unknown')
        })
    except Exception as e:
        return jsonify({'error': f'Language detection failed: {str(e)}'}), 500

@language_bp.route('/supported')
def get_supported_languages():
    """Get list of supported languages"""
    return jsonify({
        'success': True,
        'languages': translation_service.get_supported_languages()
    })

@language_bp.route('/ui-catalog/<lang>')
def get_ui_catalog(lang):
    """Public endpoint to fetch UI translation catalog for a given language.
    Intended for client-side dynamic UI updates without requiring authentication.
    """
    supported = translation_service.get_supported_languages()
    if lang not in supported:
        return jsonify({'error': 'Unsupported language'}), 400
    try:
        # Access the lightweight UI catalog from the translation service
        catalog = getattr(translation_service, 'catalog', {}).get(lang) or {}
        # Provide a minimal response to drive client-side updates
        return jsonify({
            'success': True,
            'language': lang,
            'language_name': supported.get(lang, lang),
            'catalog': catalog
        })
    except Exception as e:
        return jsonify({'error': f'Failed to load UI catalog: {str(e)}'}), 500

@language_bp.route('/auto-translate/<int:message_id>')
@login_required
def auto_translate_message(message_id):
    """Auto-translate a message to user's preferred language"""
    message = Message.query.get_or_404(message_id)
    
    # Check if user has permission to view this message
    # (This would need to be implemented based on your chat permission logic)
    
    target_lang = current_user.preferred_language
    source_lang = message.language
    
    if source_lang == target_lang:
        return jsonify({
            'success': True,
            'message': message.content,
            'already_in_target_language': True
        })
    
    try:
        translated_content = translation_service.translate_text(
            message.content, 
            source_lang, 
            target_lang
        )
        
        return jsonify({
            'success': True,
            'original_message': message.content,
            'translated_message': translated_content,
            'source_lang': source_lang,
            'target_lang': target_lang
        })
    except Exception as e:
        return jsonify({'error': f'Translation failed: {str(e)}'}), 500
