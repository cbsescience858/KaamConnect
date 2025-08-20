from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255))
    phone_number = db.Column(db.String(20))
    user_type = db.Column(db.String(20))  # 'client' or 'worker'
    preferred_language = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    jobs = db.relationship('Job', backref='creator', lazy=True)
    applications = db.relationship('JobApplication', backref='applicant', lazy=True)
    messages = db.relationship('Message', backref='sender', lazy=True)
    skills = db.relationship('UserSkill', backref='user', lazy='dynamic', cascade='all, delete-orphan')

    @property
    def first_name(self) -> str:
        """Return the first name parsed from the full username (stored as full name)."""
        if not self.username:
            return ''
        # Split by whitespace and return the first non-empty token
        for part in self.username.strip().split():
            if part:
                return part
        return ''

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class UserSkill(db.Model):
    __tablename__ = 'user_skills'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    skill = db.Column(db.String(80), nullable=False)
    experience_years = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<UserSkill {self.skill} ({self.experience_years} yrs)>'

class Job(db.Model):
    __tablename__ = 'jobs'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    budget = db.Column(db.Float)
    location = db.Column(db.String(200))
    status = db.Column(db.String(20), default='open')  # open, in_progress, completed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign Keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationships
    applications = db.relationship('JobApplication', backref='job', lazy=True)
    messages = db.relationship('Message', backref='job', lazy=True)
    
    def __repr__(self):
        return f'<Job {self.title}>'

class JobApplication(db.Model):
    __tablename__ = 'job_applications'
    
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(20), default='pending')  # pending, accepted, rejected
    offer_amount = db.Column(db.Float)
    message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign Keys
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    def __repr__(self):
        return f'<JobApplication {self.id}>'

class Message(db.Model):
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    language = db.Column(db.String(20))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign Keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id'), nullable=False)
    
    def __repr__(self):
        return f'<Message {self.id}>'
