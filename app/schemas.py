from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# ----------------------------
# Quiz Schemas
# ----------------------------
class QuestionDistribution(BaseModel):
    easy: int
    medium: int
    hard: int

class PointsStrategy(BaseModel):
    easy: float
    medium: float
    hard: float

class QuizCreate(BaseModel):
    grade: int
    subject: str
    total_questions: int
    max_score: int
    question_distribution: QuestionDistribution
    points_strategy: PointsStrategy
    difficulty: Optional[str] = None  # Kept for backward compatibility


class QuizOut(BaseModel):
    id: int
    grade: int
    subject: str
    total_questions: int
    max_score: int
    difficulty: str
    created_at: datetime

    class Config:
        orm_mode = True


# ----------------------------
# Submission Schemas
# ----------------------------
class SubmissionCreate(BaseModel):
    quiz_id: int
    user_id: int
    answers: List[str]


class SubmissionOut(BaseModel):
    id: int
    quiz_id: int
    user_id: int
    score: int
    feedback: Optional[str] = None
    submitted_at: datetime

    class Config:
        orm_mode = True


# ----------------------------
# Filter for /quiz/history
# ----------------------------
class HistoryFilter(BaseModel):
    grade: Optional[int] = None
    subject: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


# ----------------------------
# AI Hint and Adaptive Difficulty Requests
# ----------------------------
class HintRequest(BaseModel):
    question: str
    user_answer: Optional[str] = None


class AdaptiveDifficultyRequest(BaseModel):
    previous_score: float
    subject: str
    grade: int

class LeaderboardEntry(BaseModel):
    rank: int
    user_id: str
    score: float
    max_score: float
    percentage: float
    subject: str
    grade: int
    date: datetime

class LeaderboardResponse(BaseModel):
    grade: Optional[int]
    subject: Optional[str]
    entries: List[LeaderboardEntry]