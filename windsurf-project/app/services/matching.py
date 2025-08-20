from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MinMaxScaler
import numpy as np
from app.models import Job, User, JobApplication
from app import db
import logging

class JobMatchingService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1, 2))
        self.scaler = MinMaxScaler()
        
    def get_job_features(self, job):
        """Extract features from a job post"""
        # Combine title, description, and tags into a single text
        tags = ' '.join([tag.tag for tag in job.tags])
        text = f"{job.title} {job.description} {tags}"
        return text.lower()
    
    def get_user_features(self, user):
        """Extract features from a user's profile"""
        # Get user's skills and experience
        skills = ' '.join([f"{skill.skill} " * (skill.experience_years or 1) 
                          for skill in user.skills])
        
        # Get user's previous job applications for context
        applications = JobApplication.query.filter_by(user_id=user.id).all()
        job_ids = [app.job_id for app in applications if app.job_id]
        
        # Get job details from applications
        applied_jobs = Job.query.filter(Job.id.in_(job_ids)).all()
        job_texts = [f"{job.title} {job.description}" for job in applied_jobs]
        
        # Combine all features
        features = f"{skills} {' '.join(job_texts)}"
        return features.lower()
    
    def train_vectorizer(self, jobs):
        """Train the TF-IDF vectorizer on job data"""
        try:
            job_texts = [self.get_job_features(job) for job in jobs]
            self.vectorizer.fit(job_texts)
            self.logger.info("TF-IDF vectorizer trained successfully")
            return True
        except Exception as e:
            self.logger.error(f"Error training vectorizer: {str(e)}")
            return False
    
    def calculate_similarity(self, user, jobs, top_n=10):
        """
        Calculate similarity between user and jobs
        Returns: list of (job_id, similarity_score) tuples
        """
        if not jobs:
            return []
        
        try:
            # Get features
            user_features = self.get_user_features(user)
            job_texts = [self.get_job_features(job) for job in jobs]
            
            # Vectorize
            try:
                user_vec = self.vectorizer.transform([user_features])
                job_vecs = self.vectorizer.transform(job_texts)
            except ValueError:
                # If vectorizer not trained, train it first
                if self.train_vectorizer(jobs):
                    user_vec = self.vectorizer.transform([user_features])
                    job_vecs = self.vectorizer.transform(job_texts)
                else:
                    return []
            
            # Calculate cosine similarity
            similarity_scores = cosine_similarity(user_vec, job_vecs).flatten()
            
            # Normalize scores to 0-1 range
            if len(similarity_scores) > 1:
                similarity_scores = self.scaler.fit_transform(similarity_scores.reshape(-1, 1)).flatten()
            
            # Get top N matches
            job_scores = list(zip([job.id for job in jobs], similarity_scores))
            job_scores.sort(key=lambda x: x[1], reverse=True)
            
            return job_scores[:top_n]
            
        except Exception as e:
            self.logger.error(f"Error calculating job matches: {str(e)}")
            return []
    
    def get_job_recommendations(self, user, limit=20):
        """Get recommended jobs for a user"""
        try:
            # Get all open jobs that user hasn't applied to
            applied_job_ids = [app.job_id for app in user.applications]
            
            # Get jobs that match user's preferred categories if any
            user_skills = [skill.skill.lower() for skill in user.skills]
            
            # If user has skills, find jobs with matching tags
            if user_skills:
                matching_jobs = Job.query.filter(
                    Job.status == 'open',
                    Job.id.notin_(applied_job_ids),
                    Job.tags.any(JobTag.tag.in_(user_skills))
                ).all()
                
                # If not enough matches, include other jobs
                if len(matching_jobs) < limit:
                    additional_jobs = Job.query.filter(
                        Job.status == 'open',
                        Job.id.notin_(applied_job_ids + [j.id for j in matching_jobs])
                    ).limit(limit - len(matching_jobs)).all()
                    matching_jobs.extend(additional_jobs)
            else:
                # If no skills, just get recent open jobs
                matching_jobs = Job.query.filter(
                    Job.status == 'open',
                    Job.id.notin_(applied_job_ids)
                ).order_by(Job.created_at.desc()).limit(limit).all()
            
            # Calculate similarity scores
            job_scores = self.calculate_similarity(user, matching_jobs, top_n=limit)
            
            # Get job details for top matches
            job_ids = [job_id for job_id, _ in job_scores]
            jobs = {job.id: job for job in matching_jobs if job.id in job_ids}
            
            # Return jobs in order of score
            return [{
                'job': jobs[job_id],
                'score': score,
                'matching_skills': self._get_matching_skills(user, jobs[job_id])
            } for job_id, score in job_scores if job_id in jobs]
            
        except Exception as e:
            self.logger.error(f"Error getting job recommendations: {str(e)}")
            return []
    
    def _get_matching_skills(self, user, job):
        """Get list of skills that match between user and job"""
        user_skills = {skill.skill.lower() for skill in user.skills}
        job_tags = {tag.tag.lower() for tag in job.tags}
        return list(user_skills.intersection(job_tags))
    
    def get_similar_jobs(self, job_id, limit=5):
        """Get jobs similar to a given job"""
        try:
            target_job = Job.query.get_or_404(job_id)
            other_jobs = Job.query.filter(
                Job.id != job_id,
                Job.status == 'open'
            ).limit(100).all()  # Limit for performance
            
            if not other_jobs:
                return []
                
            # Calculate similarity
            target_features = self.get_job_features(target_job)
            job_texts = [self.get_job_features(job) for job in other_jobs]
            
            # Vectorize
            try:
                target_vec = self.vectorizer.transform([target_features])
                job_vecs = self.vectorizer.transform(job_texts)
            except ValueError:
                # If vectorizer not trained, train it first
                if self.train_vectorizer([target_job] + other_jobs):
                    target_vec = self.vectorizer.transform([target_features])
                    job_vecs = self.vectorizer.transform(job_texts)
                else:
                    return []
            
            # Calculate similarity
            similarity_scores = cosine_similarity(target_vec, job_vecs).flatten()
            
            # Get top matches
            job_scores = list(zip([job.id for job in other_jobs], similarity_scores))
            job_scores.sort(key=lambda x: x[1], reverse=True)
            
            # Get job details for top matches
            job_ids = [job_id for job_id, _ in job_scores[:limit]]
            jobs = {job.id: job for job in other_jobs if job.id in job_ids}
            
            return [{
                'job': jobs[job_id],
                'score': score
            } for job_id, score in job_scores if job_id in jobs]
            
        except Exception as e:
            self.logger.error(f"Error finding similar jobs: {str(e)}")
            return []

# Global instance
job_matching_service = JobMatchingService()
