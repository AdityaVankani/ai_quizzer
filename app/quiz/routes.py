# app/quiz/routes.py

from fastapi import APIRouter, HTTPException, Depends, Query, Request, status
from fastapi.responses import JSONResponse
from typing import List, Optional
import json
import uuid
from datetime import datetime
from sqlalchemy.orm import Session

from .ai_utils import (
    generate_quiz_ai,
    evaluate_quiz_ai,
    generate_hint_ai,
    suggest_difficulty_ai,
    
)
from ..database import get_db
from ..auth.deps import get_current_user
from . import crud
from .. import schemas

router = APIRouter(prefix="/quiz", tags=["Quiz"])

# Pydantic models reused (relative import from app.schemas)
from ..schemas import QuizCreate, QuizOut, SubmissionCreate, SubmissionOut, HistoryFilter, HintRequest, AdaptiveDifficultyRequest,LeaderboardResponse

# ----------------------------
# 1. Generate new quiz (AI) -- saves quiz to DB
# ----------------------------
# Inside app/quiz/routes.py

@router.post("/generate", response_model=dict)
async def generate_quiz(req: QuizCreate, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    try:
        # Validate total_questions
        total_questions = req.total_questions
        if not 5 <= total_questions <= 30:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Number of questions must be between 5 and 30, got {total_questions}"
            )
            
        if req.max_score < total_questions:
            req.max_score = total_questions
            
        print(f"\n=== Generating Quiz (Always Adaptive) ===")
        print(f"Subject: {req.subject}")

        # --- FORCE ADAPTIVE LOGIC START ---
        # We ignore the distribution sent by frontend and calculate based on history
        print("⚡ Calculating adaptive difficulty...")
        adaptive_dist = crud.get_adaptive_question_distribution(
            db, 
            user_id=current_user, 
            subject=req.subject, 
            total_questions=total_questions
        )
        
        # Use adaptive distribution, or fallback to frontend request if calculation fails (rare)
        final_distribution = adaptive_dist if adaptive_dist else {
            'easy': req.question_distribution.easy,
            'medium': req.question_distribution.medium,
            'hard': req.question_distribution.hard
        }
        print(f"⚡ Final Distribution: {final_distribution}")
        # --- FORCE ADAPTIVE LOGIC END ---
        
        # Call Gemini AI with the calculated distribution
        ai_response = generate_quiz_ai(
            grade=req.grade,
            subject=req.subject,
            question_distribution=final_distribution,
            points_strategy={
                'easy': req.points_strategy.easy,
                'medium': req.points_strategy.medium,
                'hard': req.points_strategy.hard
            }
        )
        
        if not isinstance(ai_response, dict) or 'questions' not in ai_response:
            raise HTTPException(status_code=500, detail="Failed to generate quiz: Invalid response format")
            
        questions = ai_response['questions']
        
        # Handle question count mismatch
        if len(questions) != total_questions:
            questions = questions[:total_questions]
            while len(questions) < total_questions:
                questions.append({
                    "question": f"Additional question {len(questions) + 1}",
                    "options": ["A) Option A", "B) Option B", "C) Option C", "D) Option D"],
                    "correct_option": "A",
                    "difficulty": "medium",
                    "points": req.points_strategy.medium,
                    "explanation": "Placeholder explanation."
                })
        
        # Prepare the quiz data for database
        quiz_data = {
            'user_id': current_user,
            'grade': req.grade,
            'subject': req.subject,
            'total_questions': total_questions,
            'max_score': req.max_score,
            'difficulty': "ADAPTIVE", # Explicitly mark as Adaptive
            'quiz_json': json.dumps({
                'version': '1.1',
                'metadata': {
                    'grade': req.grade,
                    'subject': req.subject,
                    'total_questions': total_questions,
                    'max_score': req.max_score,
                    'question_distribution': final_distribution, # Save the actual adaptive distribution
                    'points_strategy': req.points_strategy.dict(),
                    'generated_at': datetime.utcnow().isoformat()
                },
                'questions': questions
            }),
            'easy_questions': final_distribution.get('easy', 0),
            'medium_questions': final_distribution.get('medium', 0),
            'hard_questions': final_distribution.get('hard', 0),
            'easy_points': req.points_strategy.easy,
            'medium_points': req.points_strategy.medium,
            'hard_points': req.points_strategy.hard
        }
        
        # Save to database
        quiz = crud.create_quiz(db, current_user, quiz_data)
        db.refresh(quiz)
        
        response_data = {
            'id': quiz.id,
            'created_at': quiz.created_at.isoformat(),
            'total_questions': quiz.total_questions,
            'max_score': quiz.max_score,
            'difficulty': quiz.difficulty,
            'quiz': {
                'questions': questions,
                'metadata': {
                    'subject': quiz.subject,
                    'grade': quiz.grade,
                    'total_questions': quiz.total_questions,
                    'max_score': quiz.max_score,
                    'difficulty': quiz.difficulty,
                    'created_at': quiz.created_at.isoformat()
                }
            }
        }
        return response_data

    except Exception as e:
        print(f"Error in generate_quiz: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate quiz: {str(e)}")

# ----------------------------
# 2. Evaluate quiz answers (AI) -- saves submission
# ----------------------------
from pydantic import BaseModel

class EvalRequest(BaseModel):
    quiz_id: int
    user_answers: List[str]

@router.post("/evaluate", response_model=dict)
async def evaluate_quiz(
    req: EvalRequest, 
    db: Session = Depends(get_db), 
    current_user: str = Depends(get_current_user)
):
    """
    Evaluate quiz answers and provide detailed feedback.
    
    Args:
        req: Evaluation request containing quiz_id and user_answers
        db: Database session
        current_user: Currently authenticated user
        
    Returns:
        dict: Evaluation results including score, feedback, and suggestions
    """
    try:
        print(f"\n=== New Evaluation Request ===")
        print(f"User: {current_user}")
        print(f"Quiz ID: {req.quiz_id}")
        print(f"Number of answers: {len(req.user_answers) if req.user_answers else 0}")
        
        # Fetch quiz from DB
        Quiz = __import__("app.models", fromlist=["Quiz"]).Quiz
        quiz = db.query(Quiz).filter_by(id=req.quiz_id).first()
        
        if not quiz:
            error_msg = f"Quiz with ID {req.quiz_id} not found"
            print(error_msg)
            raise HTTPException(status_code=404, detail=error_msg)

        # Parse quiz JSON
        try:
            # First parse the JSON string if it's a string
            quiz_json = json.loads(quiz.quiz_json) if isinstance(quiz.quiz_json, str) else quiz.quiz_json
            
            # Handle different quiz data structures
            if isinstance(quiz_json, dict):
                # New format with questions in quiz.questions
                if 'questions' in quiz_json:
                    quiz_data = quiz_json['questions']
                # Legacy format where the root is the questions list
                elif 'quiz' in quiz_json and isinstance(quiz_json['quiz'], list):
                    quiz_data = quiz_json['quiz']
                else:
                    # If it's a dict but we don't have questions, try to use it as is
                    quiz_data = quiz_json
            elif isinstance(quiz_json, list):
                # Direct list of questions
                quiz_data = quiz_json
            else:
                raise ValueError(f"Unexpected quiz data format: {type(quiz_json)}")
                
            # Ensure we have a list of questions
            if not isinstance(quiz_data, list):
                raise ValueError(f"Quiz data is not a list. Got: {type(quiz_data)}")
                
            print(f"Loaded quiz with {len(quiz_data)} questions")
            
        except Exception as e:
            error_msg = f"Error parsing quiz data: {str(e)}"
            print(error_msg)
            raise HTTPException(status_code=400, detail=error_msg)

        # Validate user answers
        if not req.user_answers:
            error_msg = "No answers provided. Please submit answers for all questions."
            print(error_msg)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": error_msg,
                    "details": {
                        "answers_provided": 0,
                        "questions_expected": len(quiz_data)
                    }
                }
            )
            
        if len(req.user_answers) != len(quiz_data):
            error_msg = "Number of answers does not match number of questions"
            print(f"{error_msg}. Got {len(req.user_answers)} answers for {len(quiz_data)} questions")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": error_msg,
                    "details": {
                        "answers_provided": len(req.user_answers),
                        "questions_expected": len(quiz_data),
                        "quiz_id": req.quiz_id
                    }
                }
            )
            
        # Check for empty answers
        empty_answers = [i+1 for i, ans in enumerate(req.user_answers) if not ans.strip()]
        if empty_answers:
            error_msg = f"Please provide answers for all questions. Missing answers for questions: {', '.join(map(str, empty_answers))}"
            print(error_msg)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": error_msg,
                    "details": {
                        "empty_questions": empty_answers,
                        "total_questions": len(quiz_data)
                    }
                }
            )

        # Evaluate answers using AI
        print("Starting evaluation...")
        try:
            eval_result = evaluate_quiz_ai(quiz_data, req.user_answers)
            print(f"Evaluation complete. Score: {eval_result.get('total_score')}/{eval_result.get('max_score')}")
        except Exception as e:
            error_msg = f"Error during evaluation: {str(e)}"
            print(error_msg)
            raise HTTPException(status_code=500, detail=error_msg)

        # Prepare feedback and suggestions for storage
        feedback_data = eval_result.get("feedback", [])
        
        # Ensure we have valid feedback data
        if not feedback_data or not isinstance(feedback_data, list):
            feedback_data = []
            
        # Prepare suggestions
        suggestions = eval_result.get("suggestions", [])
        if isinstance(suggestions, list):
            suggestions = "\n".join(suggestions)
        else:
            suggestions = str(suggestions) if suggestions else ""
            
        # Calculate percentage
        percentage = 0
        if eval_result.get('max_score', 0) > 0:
            percentage = (eval_result.get('total_score', 0) / eval_result.get('max_score', 1)) * 100
            
        # Calculate performance metrics by difficulty
        performance_metrics = {
            "easy": {"correct": 0, "total": 0, "score": 0, "max_score": 0},
            "medium": {"correct": 0, "total": 0, "score": 0, "max_score": 0},
            "hard": {"correct": 0, "total": 0, "score": 0, "max_score": 0}
        }
        
        # Calculate performance by difficulty
        for i, feedback in enumerate(feedback_data):
            if i < len(quiz_data):
                question = quiz_data[i]
                difficulty = question.get("difficulty", "medium").lower()
                if difficulty not in performance_metrics:
                    difficulty = "medium"  # Default to medium if invalid
                
                performance_metrics[difficulty]["total"] += 1
                if feedback.get("is_correct", False):
                    performance_metrics[difficulty]["correct"] += 1
                
                # Add score if available
                score = feedback.get("score", 0)
                max_score = feedback.get("max_score", 0)
                performance_metrics[difficulty]["score"] += score
                performance_metrics[difficulty]["max_score"] += max_score
        
        # Build submission payload with proper data types
        submission_payload = {
            "quiz_id": req.quiz_id,
            "user_id": current_user,
            "total_score": float(eval_result.get("total_score", 0)),
            "max_score": float(eval_result.get("max_score", 1)),
            "answers_json": json.dumps(req.user_answers, ensure_ascii=False),
            "feedback_json": json.dumps(feedback_data, ensure_ascii=False),
            "suggestions": suggestions,
            "performance_metrics": json.dumps(performance_metrics, ensure_ascii=False)
        }
        
        # Save submission to database
        try:
            saved_submission = crud.create_submission(db, submission_payload)
            print(f"Submission saved with ID: {saved_submission.id}")
        except Exception as e:
            error_msg = f"Error saving submission: {str(e)}"
            print(error_msg)
            # Continue with evaluation even if saving fails
            saved_submission = type('Object', (), {
                'id': None,
                'total_score': submission_payload['total_score'],
                'max_score': submission_payload['max_score'],
                'feedback_json': submission_payload['feedback_json']
            })

        # Prepare response
        response = {
            "status": "success",
            "submission_id": saved_submission.id if hasattr(saved_submission, 'id') else None,
            "total_score": saved_submission.total_score,
            "max_score": saved_submission.max_score,
            "percentage": round(percentage, 2),
            "feedback": feedback_data,
            "suggestions": suggestions.split("\n") if suggestions else [],
            "correct_answers": eval_result.get("correct_answers", 0),
            "total_questions": len(quiz_data)
        }
        
        print(f"Evaluation response: {response}")
        return response

    except HTTPException as http_exc:
        print(f"HTTP Exception: {str(http_exc)}")
        raise http_exc
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(error_msg)
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=error_msg)


# ----------------------------
# 3. Get AI hint for a question
# ----------------------------
class HintResponse(BaseModel):
    question: str
    hint: str
    success: bool = True
    
    class Config:
        schema_extra = {
            "example": {
                "question": "What is the capital of France?",
                "hint": "Think about a famous European city known for the Eiffel Tower.",
                "success": True
            }
        }

@router.post(
    "/hint", 
    response_model=HintResponse,
    responses={
        400: {"description": "Invalid request - missing or invalid question text"},
        500: {"description": "Error generating hint"}
    }
)
async def get_hint(
    request: Request,
    req: HintRequest, 
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate a helpful hint for a quiz question.
    
    This endpoint provides guidance for a given quiz question without revealing the answer.
    It can also consider the user's current answer (if provided) to give more targeted hints.
    """
    try:
        # Log the incoming request
        print(f"\n=== New Hint Request ===")
        print(f"User: {current_user}")
        print(f"Question: {req.question}")
        print(f"User answer: {req.user_answer}")
        
        # Validate input
        if not req.question or not req.question.strip():
            error_msg = "Question text is required"
            print(f"Validation error: {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
            
        # Generate the hint using AI
        try:
            print("Generating hint with AI...")
            hint = generate_hint_ai(
                question_text=req.question.strip(),
                user_answer=req.user_answer.strip() if req.user_answer else None
            )
            
            if not hint:
                error_msg = "AI returned an empty hint"
                print(f"Error: {error_msg}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=error_msg
                )
            
            print(f"Successfully generated hint: {hint[:100]}...")
            
            return {
                "question": req.question.strip(),
                "hint": hint,
                "success": True
            }
            
        except Exception as ai_error:
            # Log the specific AI error
            error_msg = f"AI error in hint generation: {str(ai_error)}"
            print(error_msg)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate hint due to an AI service error"
            )
            
    except HTTPException as http_error:
        # Re-raise HTTP exceptions
        raise http_error
        
    except Exception as e:
        # Log unexpected errors
        error_id = str(uuid.uuid4())[:8]
        error_msg = f"An unexpected error occurred (ID: {error_id}). Please try again later."
        print(f"Error ID: {error_id}, Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        )
        
        # Validate input
        question_text = (req.question or "").strip()
        if not question_text:
            error_msg = "Question text is required"
            print(f"Validation error: {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        
        try:
            print("Generating hint with AI...")
            # Generate the hint using AI
            hint = generate_hint_ai(
                question_text=question_text,
                user_answer=req.user_answer if req.user_answer else None
            )
            
            if not hint:
                error_msg = "AI returned an empty hint"
                print(f"Error: {error_msg}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=error_msg
                )
            
            print(f"Successfully generated hint: {hint[:100]}...")
            
            return {
                "question": question_text,
                "hint": hint,
                "success": True
            }
            
        except Exception as ai_error:
            # Log the specific AI error
            print(f"AI error in hint generation: {str(ai_error)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate hint due to an AI service error"
            )
            
    except HTTPException as http_error:
        # Re-raise HTTP exceptions
        raise http_error
        
    except Exception as e:
        # Log unexpected errors
        error_id = str(uuid.uuid4())[:8]
        print(f"Error ID: {error_id}, Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred (ID: {error_id}). Please try again later."
        )


# ----------------------------
# 4. Adaptive difficulty (automated using stored history)
# ----------------------------
@router.post("/next_difficulty", response_model=dict)
def get_next_difficulty(req: AdaptiveDifficultyRequest, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    try:
        # If subject context is desired we can fetch latest score for the subject specifically
        latest_percentage = crud.get_latest_score_for_user(db, current_user)
        if latest_percentage is None:
            # fallback to provided previous_score
            next_level = suggest_difficulty_ai(req.previous_score)
            return {"previous_score": req.previous_score, "next_difficulty": next_level}
        else:
            next_level = suggest_difficulty_ai(latest_percentage)
            return {"previous_score": latest_percentage, "next_difficulty": next_level}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error suggesting difficulty: {str(e)}")


# ----------------------------
# 5. /quiz/history endpoint (filters)
# ----------------------------
@router.get("/history", response_model=dict)
def quiz_history(
    user_id: Optional[str] = Query(None, description="Filter by user ID (defaults to current user)"),
    grade: Optional[int] = Query(None, ge=1, le=12, description="Filter by grade level (1-12)"),
    subject: Optional[str] = Query(None, min_length=1, description="Filter by subject (case-insensitive partial match)"),
    min_marks: Optional[float] = Query(None, ge=0, description="Filter by minimum score"),
    max_marks: Optional[float] = Query(None, ge=0, description="Filter by maximum score"),
    from_date: Optional[str] = Query(
        None, 
        regex=r'^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})?)?$',
        description="Filter by start date (YYYY-MM-DD or ISO format)"
    ),
    to_date: Optional[str] = Query(
        None, 
        regex=r'^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})?)?$',
        description="Filter by end date (YYYY-MM-DD or ISO format)"
    ),
    limit: int = Query(50, ge=1, le=100, description="Number of items per page (1-100)"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    try:
        # Default user_id to current_user if not provided
        user_id = user_id or current_user
        
        # Validate date range if both are provided
        if from_date and to_date:
            try:
                from_dt = from_date if 'T' in from_date else f"{from_date}T00:00:00"
                to_dt = to_date if 'T' in to_date else f"{to_date}T23:59:59.999999"
                if from_dt > to_dt:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="'from_date' must be before or equal to 'to_date'"
                    )
            except (ValueError, TypeError) as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid date format: {str(e)}"
                )
        
        # Validate score range if both are provided
        if min_marks is not None and max_marks is not None and min_marks > max_marks:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="'min_marks' must be less than or equal to 'max_marks'"
            )

        # Prepare filters dictionary
        filters = {
            "user_id": user_id,
            "grade": grade,
            "subject": subject.strip() if subject and isinstance(subject, str) else None,
            "min_marks": float(min_marks) if min_marks is not None else None,
            "max_marks": float(max_marks) if max_marks is not None else None,
            "from_date": from_date,
            "to_date": to_date,
            "limit": limit,
            "offset": offset
        }

        total, items = crud.get_submissions_by_filters(db, filters)

        # Convert ORM objects to dicts with proper error handling
        out = []
        for s in items:
            try:
                # Safely parse JSON data with error handling
                answers = json.loads(s.answers_json) if s.answers_json else None
                
                # Parse feedback JSON with error handling
                feedback = None
                if s.feedback_json:
                    try:
                        feedback = json.loads(s.feedback_json)
                    except json.JSONDecodeError:
                        feedback = {"error": "Could not parse feedback data"}
                
                # Calculate percentage safely
                percentage = None
                if s.max_score and s.max_score > 0:
                    percentage = round((s.total_score / s.max_score) * 100, 2)
                
                # Include quiz details if available
                quiz_data = None
                if hasattr(s, 'quiz') and s.quiz:
                    try:
                        quiz_data = {
                            "subject": s.quiz.subject,
                            "grade": s.quiz.grade,
                            "difficulty": s.quiz.difficulty,
                            "total_questions": s.quiz.total_questions
                        }
                    except Exception as e:
                        print(f"Error getting quiz data: {str(e)}")
                
                out.append({
                    "id": s.id,
                    "quiz_id": s.quiz_id,
                    "user_id": s.user_id,
                    "total_score": float(s.total_score) if s.total_score is not None else 0,
                    "max_score": float(s.max_score) if s.max_score is not None else 1,
                    "percentage": percentage,
                    "answers": answers,
                    "feedback": feedback,
                    "suggestions": s.suggestions.split('\n') if s.suggestions else [],
                    "created_at": s.created_at.isoformat() if s.created_at else None,
                    "quiz": quiz_data
                })
                
            except Exception as e:
                print(f"Error processing submission {s.id}: {str(e)}")
                continue  # Skip this item but continue with others

        return {"total": total, "count": len(out), "results": out}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching history: {str(e)}")

# ... existing imports ...
# Ensure LeaderboardResponse is imported from schemas if you moved imports to the top, 
# or just ensure schemas.* works.

# ----------------------------
# 7. Leaderboard Endpoint
# ----------------------------
@router.get("/leaderboard", response_model=schemas.LeaderboardResponse)
def get_leaderboard(
    grade: Optional[int] = Query(None, ge=1, le=12, description="Filter by grade"),
    subject: Optional[str] = Query(None, description="Filter by subject"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    try:
        items = crud.get_leaderboard_data(db, grade, subject, limit)
        
        entries = []
        for idx, item in enumerate(items, 1):
            # Calculate percentage
            pct = 0.0
            if item.max_score > 0:
                pct = round((item.total_score / item.max_score) * 100, 1)
            
            entries.append({
                "rank": idx,
                "user_id": item.user_id, # In a real app, you might fetch a username here
                "score": item.total_score,
                "max_score": item.max_score,
                "percentage": pct,
                "subject": item.quiz.subject if item.quiz else "Unknown",
                "grade": item.quiz.grade if item.quiz else 0,
                "date": item.created_at
            })
            
        return {
            "grade": grade,
            "subject": subject,
            "entries": entries
        }
    except Exception as e:
        print(f"Leaderboard Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch leaderboard")