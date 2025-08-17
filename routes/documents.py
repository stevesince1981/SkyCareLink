import os
import hashlib
import logging
from datetime import datetime
from flask import Blueprint, request, jsonify, render_template, send_file, session, abort
from werkzeug.utils import secure_filename
from io import BytesIO

from consumer_main_final import consumer_app as app, db

logger = logging.getLogger(__name__)

# Create documents blueprint
documents_bp = Blueprint('documents', __name__, url_prefix='/quotes')

# Database availability
DB_AVAILABLE = True
try:
    from models.document import Document
    from models.audit import AuditLog
    from models import Quote
except ImportError:
    DB_AVAILABLE = False
    logger.warning("Document models not available - document features will be limited")

# File upload configuration
ALLOWED_EXTENSIONS = {
    'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 
    'xls', 'xlsx', 'ppt', 'pptx', 'zip', 'rar', 'csv', 'json'
}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB per file
MAX_FILES_PER_REQUEST = 10

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def calculate_file_hash(file_data):
    """Calculate SHA-256 hash of file data"""
    return hashlib.sha256(file_data).hexdigest()

@documents_bp.route('/<quote_ref>/docs', methods=['GET'])
def list_documents(quote_ref):
    """List all documents for a quote"""
    try:
        documents = []
        
        if DB_AVAILABLE:
            # Verify quote exists
            quote = Quote.query.filter_by(ref_id=quote_ref).first()
            if not quote:
                abort(404, description="Quote not found")
            
            # Get all documents for this quote
            documents = Document.query.filter_by(quote_ref=quote_ref).order_by(
                Document.uploaded_at.desc()
            ).all()
            
            # Convert to dictionaries for JSON response
            documents_data = [doc.to_dict() for doc in documents]
        else:
            # Demo data if database not available
            documents_data = [
                {
                    'id': 1,
                    'quote_ref': quote_ref,
                    'filename': 'medical_records.pdf',
                    'original_filename': 'patient_medical_records.pdf',
                    'content_type': 'application/pdf',
                    'file_size': 245760,
                    'file_size_human': '240.0 KB',
                    'uploaded_by': 'hospital_user',
                    'upload_source': 'web',
                    'uploaded_at': '2025-08-17T10:30:00',
                    'file_hash': 'a1b2c3d4e5f6...'
                },
                {
                    'id': 2,
                    'quote_ref': quote_ref,
                    'filename': 'insurance_card.jpg',
                    'original_filename': 'insurance_card_front.jpg',
                    'content_type': 'image/jpeg',
                    'file_size': 512000,
                    'file_size_human': '500.0 KB',
                    'uploaded_by': 'family_user',
                    'upload_source': 'web',
                    'uploaded_at': '2025-08-17T11:15:00',
                    'file_hash': 'b2c3d4e5f6g7...'
                }
            ]
        
        # Return JSON for API or render template for web
        if request.headers.get('Accept') == 'application/json':
            return jsonify({
                'success': True,
                'quote_ref': quote_ref,
                'document_count': len(documents_data),
                'documents': documents_data
            })
        else:
            return render_template('quotes/documents.html', 
                                 quote_ref=quote_ref, 
                                 documents=documents_data)
        
    except Exception as e:
        logger.error(f"Error listing documents for {quote_ref}: {str(e)}")
        if request.headers.get('Accept') == 'application/json':
            return jsonify({'success': False, 'error': 'Internal server error'}), 500
        else:
            return render_template('error.html', 
                                 message="Error loading documents"), 500

@documents_bp.route('/<quote_ref>/docs', methods=['POST'])
def upload_documents(quote_ref):
    """Upload multiple documents for a quote (immutable storage)"""
    try:
        if not DB_AVAILABLE:
            return jsonify({'success': False, 'error': 'Database not available'}), 503
        
        # Verify quote exists
        quote = Quote.query.filter_by(ref_id=quote_ref).first()
        if not quote:
            return jsonify({'success': False, 'error': 'Quote not found'}), 404
        
        # Check if files were uploaded
        if 'files' not in request.files:
            return jsonify({'success': False, 'error': 'No files provided'}), 400
        
        files = request.files.getlist('files')
        
        # Validate file count
        if len(files) > MAX_FILES_PER_REQUEST:
            return jsonify({
                'success': False, 
                'error': f'Too many files. Maximum {MAX_FILES_PER_REQUEST} files per request'
            }), 400
        
        uploaded_documents = []
        errors = []
        
        # Get user information
        user_id = session.get('user_id', 'anonymous')
        user_role = session.get('role', 'unknown')
        
        for file in files:
            if file.filename == '':
                errors.append('Empty filename provided')
                continue
            
            # Validate file
            if not allowed_file(file.filename):
                errors.append(f'File type not allowed: {file.filename}')
                continue
            
            # Read file data
            file_data = file.read()
            
            # Validate file size
            if len(file_data) > MAX_FILE_SIZE:
                errors.append(f'File too large: {file.filename} ({len(file_data)} bytes)')
                continue
            
            if len(file_data) == 0:
                errors.append(f'Empty file: {file.filename}')
                continue
            
            # Generate secure filename
            original_filename = file.filename
            secure_name = secure_filename(file.filename)
            
            # Add timestamp to prevent conflicts
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            filename_parts = secure_name.rsplit('.', 1)
            if len(filename_parts) == 2:
                unique_filename = f"{filename_parts[0]}_{timestamp}.{filename_parts[1]}"
            else:
                unique_filename = f"{secure_name}_{timestamp}"
            
            # Calculate file hash
            file_hash = calculate_file_hash(file_data)
            
            # Create document record
            try:
                document = Document(
                    quote_ref=quote_ref,
                    filename=unique_filename,
                    original_filename=original_filename,
                    content_type=file.content_type or 'application/octet-stream',
                    file_size=len(file_data),
                    file_data=file_data,
                    uploaded_by=user_id,
                    upload_source='web',
                    file_hash=file_hash
                )
                
                db.session.add(document)
                db.session.flush()  # Get ID before commit
                
                # Log the upload
                AuditLog.log_event(
                    event_type='document_upload',
                    entity_type='document',
                    entity_id=document.id,
                    action='created',
                    description=f'Document uploaded: {original_filename} for quote {quote_ref}',
                    user_id=user_id,
                    user_role=user_role,
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent', '')[:500],
                    new_values={
                        'filename': unique_filename,
                        'original_filename': original_filename,
                        'file_size': len(file_data),
                        'content_type': file.content_type
                    }
                )
                
                uploaded_documents.append(document.to_dict())
                logger.info(f"Document uploaded: {original_filename} -> {unique_filename} for {quote_ref}")
                
            except Exception as e:
                logger.error(f"Error saving document {original_filename}: {str(e)}")
                errors.append(f'Failed to save: {original_filename}')
                continue
        
        # Commit all changes
        if uploaded_documents:
            db.session.commit()
        
        # Prepare response
        response_data = {
            'success': len(uploaded_documents) > 0,
            'quote_ref': quote_ref,
            'uploaded_count': len(uploaded_documents),
            'total_submitted': len(files),
            'documents': uploaded_documents
        }
        
        if errors:
            response_data['errors'] = errors
            response_data['error_count'] = len(errors)
        
        status_code = 200 if uploaded_documents else 400
        return jsonify(response_data), status_code
        
    except Exception as e:
        logger.error(f"Error uploading documents for {quote_ref}: {str(e)}")
        if DB_AVAILABLE:
            db.session.rollback()
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@documents_bp.route('/<quote_ref>/docs/<int:doc_id>', methods=['GET'])
def download_document(quote_ref, doc_id):
    """Download a specific document"""
    try:
        if not DB_AVAILABLE:
            abort(503, description="Database not available")
        
        # Get document
        document = Document.query.filter_by(id=doc_id, quote_ref=quote_ref).first()
        if not document:
            abort(404, description="Document not found")
        
        # Log the download
        AuditLog.log_event(
            event_type='document_download',
            entity_type='document',
            entity_id=document.id,
            action='accessed',
            description=f'Document downloaded: {document.original_filename}',
            user_id=session.get('user_id', 'anonymous'),
            user_role=session.get('role', 'unknown'),
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')[:500]
        )
        db.session.commit()
        
        # Return file data
        return send_file(
            BytesIO(document.file_data),
            mimetype=document.content_type,
            as_attachment=True,
            download_name=document.original_filename
        )
        
    except Exception as e:
        logger.error(f"Error downloading document {doc_id} for {quote_ref}: {str(e)}")
        abort(500, description="Internal server error")

@documents_bp.route('/<quote_ref>/docs/<int:doc_id>', methods=['DELETE'])
def delete_document(quote_ref, doc_id):
    """Attempt to delete a document - ALWAYS returns 405 Method Not Allowed"""
    # Immutable storage - deletion is not allowed
    return jsonify({
        'success': False,
        'error': 'Document deletion is not allowed',
        'message': 'Documents are immutable and cannot be deleted for audit compliance'
    }), 405

@documents_bp.route('/<quote_ref>/docs/delete/<int:doc_id>', methods=['GET', 'POST', 'DELETE'])
def delete_document_any_method(quote_ref, doc_id):
    """Any attempt to delete documents returns 405"""
    return jsonify({
        'success': False,
        'error': 'Document deletion is not allowed',
        'message': 'Documents are immutable and cannot be deleted for audit compliance'
    }), 405