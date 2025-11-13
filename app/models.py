# app/models.py
from sqlalchemy import Column, Integer, String, DateTime, Text, Float, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class Quiz(Base):
    __tablename__ = "quizzes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)     # username (from mock login token)
    grade = Column(Integer, index=True)
    subject = Column(String, index=True)
    total_questions = Column(Integer)
    max_score = Column(Integer)
    difficulty = Column(String, index=True)
    quiz_json = Column(Text)                 # JSON string of generated quiz
    
    # New fields for question distribution and points strategy
    easy_questions = Column(Integer, default=0)
    medium_questions = Column(Integer, default=0)
    hard_questions = Column(Integer, default=0)
    easy_points = Column(Float, default=1.0)
    medium_points = Column(Float, default=2.0)
    hard_points = Column(Float, default=3.0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    submissions = relationship("Submission", back_populates="quiz")


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"))
    user_id = Column(String, index=True)
    total_score = Column(Float)
    max_score = Column(Float)
    answers_json = Column(Text)              # JSON string of user's answers
    feedback_json = Column(Text)             # JSON string of feedback
    suggestions = Column(Text)               # AI suggestions text
    performance_metrics = Column(Text)       # JSON string with performance by difficulty
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    quiz = relationship("Quiz", back_populates="submissions")