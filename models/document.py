from datetime import datetime
from consumer_main_final import consumer_app as app, db

class Document(db.Model):
    """Immutable document storage model"""
    __tablename__ = 'documents'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Reference to quote
    quote_ref = db.Column(db.String(50), nullable=False, index=True)
    
    # File information
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    content_type = db.Column(db.String(100), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    
    # File content as BLOB
    file_data = db.Column(db.LargeBinary, nullable=False)
    
    # Upload metadata
    uploaded_by = db.Column(db.String(100))  # User identifier
    upload_source = db.Column(db.String(50), default='web')  # web, api, email, etc.
    
    # Immutable timestamps
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # File hash for integrity
    file_hash = db.Column(db.String(64))  # SHA-256 hash
    
    def __repr__(self):
        return f'<Document {self.filename} for {self.quote_ref}>'
    
    @property
    def file_size_human(self):
        """Human-readable file size"""
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'quote_ref': self.quote_ref,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'content_type': self.content_type,
            'file_size': self.file_size,
            'file_size_human': self.file_size_human,
            'uploaded_by': self.uploaded_by,
            'upload_source': self.upload_source,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None,
            'file_hash': self.file_hash
        }