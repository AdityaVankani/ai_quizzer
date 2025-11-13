# app/quiz/crud.py
from sqlalchemy.orm import Session
from .. import models
import json
from sqlalchemy import func
from datetime import datetime

def create_quiz(db: Session, user_id: str, quiz_payload: dict):
    """
    Create a new quiz with the provided payload.
    
    Args:
        db: Database session
        user_id: ID of the user creating the quiz
        quiz_payload: Dictionary containing quiz data including:
            - grade: Grade level of the quiz
            - subject: Subject of the quiz
            - total_questions: Total number of questions
            - max_score: Maximum possible score
            - difficulty: Overall difficulty (legacy, now using question distribution)
            - quiz_json: JSON string of the quiz content
            - question_distribution: Dict with keys 'easy', 'medium', 'hard' and counts
            - points_strategy: Dict with points for 'easy', 'medium', 'hard' questions
    """
    # Extract question distribution and points strategy
    question_dist = quiz_payload.get('question_distribution', {})
    points_strat = quiz_payload.get('points_strategy', {})
    
    # Create the quiz with all fields
    q = models.Quiz(
        user_id=user_id,
        grade=quiz_payload["grade"],
        subject=quiz_payload["subject"],
        total_questions=quiz_payload["total_questions"],
        max_score=quiz_payload["max_score"],
        difficulty=quiz_payload.get("difficulty", "MIXED"),
        quiz_json=quiz_payload["quiz_json"],
        # Question distribution
        easy_questions=question_dist.get('easy', 0),
        medium_questions=question_dist.get('medium', 0),
        hard_questions=question_dist.get('hard', 0),
        # Points strategy
        easy_points=points_strat.get('easy', 1.0),
        medium_points=points_strat.get('medium', 2.0),
        hard_points=points_strat.get('hard', 3.0)
    )
    db.add(q)
    db.commit()
    db.refresh(q)
    return q

def create_submission(db: Session, submission_payload: dict):
    s = models.Submission(
        quiz_id=submission_payload["quiz_id"],
        user_id=submission_payload["user_id"],
        total_score=submission_payload["total_score"],
        max_score=submission_payload["max_score"],
        answers_json=submission_payload["answers_json"],
        feedback_json=submission_payload["feedback_json"],
        suggestions=submission_payload.get("suggestions"),
        performance_metrics=submission_payload.get("performance_metrics", "{}")
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return s

def get_submissions_by_filters(db: Session, filters: dict):
    # Start with a base query that joins Submission with Quiz
    query = db.query(models.Submission).join(models.Quiz)
    
    # Apply user filter
    if filters.get("user_id"):
        query = query.filter(models.Submission.user_id == filters["user_id"])
    
    # Apply grade filter if provided
    if filters.get("grade") is not None:
        try:
            grade = int(filters["grade"])
            query = query.filter(models.Quiz.grade == grade)
        except (ValueError, TypeError):
            # If grade is not a valid integer, ignore the filter
            pass
    
    # Apply subject filter if provided (case-insensitive partial match)
    subject = filters.get("subject")
    if subject and isinstance(subject, str) and subject.strip():
        query = query.filter(models.Quiz.subject.ilike(f"%{subject.strip()}%"))
    
    # Apply score range filters
    min_marks = filters.get("min_marks")
    if min_marks is not None:
        try:
            min_marks = float(min_marks)
            query = query.filter(models.Submission.total_score >= min_marks)
        except (ValueError, TypeError):
            pass
    
    max_marks = filters.get("max_marks")
    if max_marks is not None:
        try:
            max_marks = float(max_marks)
            query = query.filter(models.Submission.total_score <= max_marks)
        except (ValueError, TypeError):
            pass
    
    # Apply date range filters
    from_date = filters.get("from_date")
    if from_date:
        try:
            # Handle both date strings with and without time
            if 'T' in from_date:
                from_dt = datetime.fromisoformat(from_date.replace('Z', '+00:00'))
            else:
                from_dt = datetime.fromisoformat(from_date)
                from_dt = from_dt.replace(hour=0, minute=0, second=0, microsecond=0)
            query = query.filter(models.Submission.created_at >= from_dt)
        except (ValueError, TypeError) as e:
            print(f"Invalid from_date format: {from_date}, error: {str(e)}")
    
    to_date = filters.get("to_date")
    if to_date:
        try:
            if 'T' in to_date:
                to_dt = datetime.fromisoformat(to_date.replace('Z', '+00:00'))
            else:
                to_dt = datetime.fromisoformat(to_date)
                to_dt = to_dt.replace(hour=23, minute=59, second=59, microsecond=999999)
            query = query.filter(models.Submission.created_at <= to_dt)
        except (ValueError, TypeError) as e:
            print(f"Invalid to_date format: {to_date}, error: {str(e)}")
    
    # Get total count before applying pagination
    total = query.count()
    
    # Apply pagination
    try:
        offset = max(0, int(filters.get("offset", 0)))
        limit = min(100, max(1, int(filters.get("limit", 50))))  # Limit max page size to 100
    except (ValueError, TypeError):
        offset = 0
        limit = 50
    
    # Execute the query with ordering and pagination
    items = query.order_by(
        models.Submission.created_at.desc()
    ).offset(offset).limit(limit).all()
    
    return total, items

def get_latest_score_for_user(db: Session, user_id: str, subject: str = None):
    """Get the latest score for a user, optionally filtered by subject."""
    query = db.query(models.Submission).filter(models.Submission.user_id == user_id)
    if subject:
        query = query.join(models.Quiz).filter(models.Quiz.subject.ilike(f"%{subject}%"))
    submission = query.order_by(models.Submission.created_at.desc()).first()
    return submission.total_score if submission else None

def get_adaptive_question_distribution(db: Session, user_id: str, subject: str, total_questions: int):
    """
    Calculate the distribution of question difficulties based on user's previous performance.
    
    Args:
        db: Database session
        user_id: ID of the user
        subject: Subject of the quiz
        total_questions: Total number of questions in the quiz
        
    Returns:
        dict: Distribution of questions by difficulty level
    """
    # Get user's previous submissions for this subject
    submissions = (
        db.query(models.Submission)
        .join(models.Quiz)
        .filter(
            models.Submission.user_id == user_id,
            models.Quiz.subject.ilike(f"%{subject}%")
        )
        .order_by(models.Submission.created_at.desc())
        .limit(3)  # Consider last 3 quizzes
        .all()
    )
    
    if not submissions:
        # First quiz - start with a balanced distribution
        return {
            'easy': int(total_questions * 0.5),  # 50% easy
            'medium': int(total_questions * 0.3),  # 30% medium
            'hard': max(1, total_questions - int(total_questions * 0.5) - int(total_questions * 0.3))  # 20% hard
        }
    
    # Calculate average performance
    total_score = 0
    max_possible = 0
    
    for sub in submissions:
        total_score += sub.total_score
        max_possible += sub.max_score
    
    performance_ratio = total_score / max_possible if max_possible > 0 else 0.5
    
    # Adjust distribution based on performance
    if performance_ratio > 0.8:  # Doing well - increase difficulty
        return {
            'easy': max(1, int(total_questions * 0.2)),  # 20% easy
            'medium': int(total_questions * 0.4),  # 40% medium
            'hard': max(1, total_questions - int(total_questions * 0.2) - int(total_questions * 0.4))  # 40% hard
        }
    elif performance_ratio > 0.5:  # Average performance - balanced
        return {
            'easy': int(total_questions * 0.4),  # 40% easy
            'medium': int(total_questions * 0.4),  # 40% medium
            'hard': max(1, total_questions - int(total_questions * 0.4) - int(total_questions * 0.4))  # 20% hard
        }
    else:  # Struggling - easier questions
        return {
            'easy': int(total_questions * 0.6),  # 60% easy
            'medium': int(total_questions * 0.3),  # 30% medium
            'hard': max(1, total_questions - int(total_questions * 0.6) - int(total_questions * 0.3))  # 10% hard
        }
    
# ... existing code ...

def get_leaderboard_data(db: Session, grade: int = None, subject: str = None, limit: int = 10):
    """
    Fetch top submissions based on score (and tie-break with date).
    """
    # Start Query: Join Submission -> Quiz
    query = db.query(models.Submission).join(models.Quiz)

    # Apply Filters
    if grade:
        query = query.filter(models.Quiz.grade == grade)
    if subject:
        query = query.filter(models.Quiz.subject.ilike(f"%{subject}%"))

    # Sort Logic:
    # 1. Highest Score first
    # 2. If scores match, highest Max Score (harder quiz)
    # 3. If both match, most recent date
    query = query.order_by(
        models.Submission.total_score.desc(),
        models.Submission.max_score.desc(),
        models.Submission.created_at.desc()
    )

    return query.limit(limit).all()