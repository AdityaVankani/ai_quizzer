# app/quiz/ai_utils.py

import os
import json
import random
from typing import Optional, Dict, List, Any, Union
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Create the model instance (use Gemini 1.5-flash for speed)
model = genai.GenerativeModel("gemini-2.0-flash")


# ----------------------------
# 🔹 1. Generate quiz questions
# ----------------------------
def generate_quiz_ai(grade, subject, question_distribution, points_strategy, **kwargs):
    """
    Generate quiz questions based on the specified distribution and points strategy,
    including detailed explanations for the answers.
    """
    total_questions = sum(question_distribution.values())
    
    def generate_questions():
        """Generate questions using the AI model"""
        prompt = f"""
        You are an expert {subject} teacher for grade {grade} students. 
        Create an engaging and educational quiz with the following specifications:
        
        SUBJECT: {subject}
        GRADE LEVEL: {grade}
        
        QUESTION DISTRIBUTION:
        - Easy questions: {question_distribution['easy']} question(s) - {points_strategy['easy']} point(s) each
        - Medium questions: {question_distribution['medium']} question(s) - {points_strategy['medium']} point(s) each
        - Hard questions: {question_distribution['hard']} question(s) - {points_strategy['hard']} point(s) each
        
        INSTRUCTIONS:
        1. Generate questions that are appropriate for grade {grade} {subject} students.
        2. For each question:
           - Write a clear, concise question.
           - Provide 4 answer choices (A-D).
           - Mark the correct answer (A, B, C, or D).
           - Specify the difficulty level (easy, medium, hard).
           - Include the points value based on difficulty.
           - **CRITICAL**: Provide a concise "explanation" for why the correct answer is right.
        3. Make sure all questions are different and cover various topics.
        
        FORMAT YOUR RESPONSE AS VALID JSON with this structure:
        {{
            "questions": [
                {{
                    "question": "Your question here",
                    "options": ["A) Option 1", "B) Option 2", "C) Option 3", "D) Option 4"],
                    "correct_option": "A",
                    "difficulty": "easy",
                    "points": {points_strategy['easy']},
                    "explanation": "The explanation for why A is correct goes here."
                }}
            ]
        }}
        
        Now, generate {total_questions} questions following these guidelines.
        """

        try:
            print("Sending request to AI model...")
            response = model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.9,
                    "top_p": 0.95,
                    "top_k": 40,
                    "max_output_tokens": 4000, # Increased to accommodate explanations
                },
            )
            
            if not response or not hasattr(response, 'text') or not response.text:
                raise ValueError("Empty response from AI model")
                
            text = response.text.strip()
            print(f"Raw AI response: {text[:200]}...") 
            
            # Clean up the response
            text = text.replace("```json", "").replace("```", "").strip()
            
            # Parse and validate the response
            data = json.loads(text)
            if not isinstance(data, dict) or 'questions' not in data:
                raise ValueError("Invalid response format: missing 'questions' key")
                
            questions = data['questions']
            if not isinstance(questions, list):
                raise ValueError("Questions must be a list")
                
            # Validate each question
            required_fields = ['question', 'options', 'correct_option', 'difficulty', 'points', 'explanation']
            for q in questions:
                if not all(k in q for k in required_fields):
                    raise ValueError(f"Missing required question fields. Found: {q.keys()}")
                if q['correct_option'] not in ['A', 'B', 'C', 'D']:
                    raise ValueError("correct_option must be A, B, C, or D")
                if q['difficulty'] not in ['easy', 'medium', 'hard']:
                    raise ValueError("difficulty must be easy, medium, or hard")
                
            print(f"Successfully generated {len(questions)} questions")
            return data
            
        except json.JSONDecodeError as e:
            print(f"Failed to parse AI response: {str(e)}")
            print(f"Response was: {text}")
            raise ValueError("Failed to parse AI response") from e
            
        except Exception as e:
            print(f"Error generating questions: {str(e)}")
            raise

    # Retry logic
    max_retries = 2
    for attempt in range(max_retries):
        try:
            return generate_questions()
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {str(e)}")
            if attempt == max_retries - 1:
                # Fallback logic if generation fails repeatedly
                # (You can keep your existing fallback logic here if you wish)
                print("All attempts failed.")
                raise
            print("Retrying...")
    
    return {"questions": []}
    
    # Try to generate questions with retries
    max_retries = 2
    for attempt in range(max_retries):
        try:
            return generate_questions()
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {str(e)}")
            if attempt == max_retries - 1:
                print("All attempts failed, using fallback questions")
                break
            print("Retrying...")
    
    # Fallback to simple questions if all retries fail
    questions = []
    question_num = 1
    
    # Generate easy questions
    for i in range(question_distribution['easy']):
        questions.append({
            "question": f"What is {random.randint(1, 10)} + {random.randint(1, 10)}?",
            "options": [
                f"A) {random.randint(1, 20)}",
                f"B) {random.randint(1, 20)}",
                f"C) {random.randint(1, 20)}",
                f"D) {random.randint(1, 20)}"
            ],
            "correct_option": random.choice(['A', 'B', 'C', 'D']),
            "difficulty": "easy",
            "points": points_strategy['easy']
        })
    
    # Generate medium questions
    for i in range(question_distribution['medium']):
        a, b = random.randint(10, 50), random.randint(1, 20)
        questions.append({
            "question": f"If you have {a} apples and give away {b}, how many do you have left?",
            "options": [
                f"A) {a - b}",
                f"B) {a + b}",
                f"C) {b - a}",
                f"D) {a * b}"
            ],
            "correct_option": "A",
            "difficulty": "medium",
            "points": points_strategy['medium']
        })
    
    # Generate hard questions
    for i in range(question_distribution['hard']):
        a, b = random.randint(2, 12), random.randint(2, 12)
        questions.append({
            "question": f"What is {a} × {b}?",
            "options": [
                f"A) {a * b}",
                f"B) {a + b}",
                f"C) {a - b if a > b else b - a}",
                f"D) {a * (b + 1)}"
            ],
            "correct_option": "A",
            "difficulty": "hard",
            "points": points_strategy['hard']
        })
    
    # Shuffle questions to mix difficulties
    random.shuffle(questions)
    
    return {"questions": questions}


# ----------------------------
# 🔹 2. Evaluate submitted answers
# ----------------------------
def evaluate_quiz_ai(quiz_data, user_answers):
    """
    Evaluate quiz answers and provide detailed feedback including explanations.
    """
    if not quiz_data or not user_answers or len(quiz_data) != len(user_answers):
        raise ValueError("Invalid input: quiz_data and user_answers must be non-empty and of equal length")
        
    total_score = 0
    max_score = 0
    correct_answers = 0
    feedback_list = []
    incorrect_questions = []
    
    # First pass: Calculate max_score and validate marks
    for i, q in enumerate(quiz_data):
        if not isinstance(q, dict):
            q = {"question": f"Question {i+1}", "options": [], "correct_option": "", "marks": 1}
        question_marks = q.get("marks", q.get("points", 1)) # Handle both 'marks' and 'points' keys
        max_score += question_marks
    
    # Process each question and answer
    for i, (q, user_ans) in enumerate(zip(quiz_data, user_answers)):
        # Ensure question has required fields
        if not isinstance(q, dict):
            q = {"question": f"Question {i+1}", "options": [], "correct_option": "", "marks": 1}
        
        # Set default values for required fields
        question_marks = q.get("marks", q.get("points", 1))
        question_text = q.get("question", f"Question {i+1}")
        options = q.get("options", [])
        correct_opt = str(q.get("correct_option", "")).strip().upper()
        
        # Find the correct option text
        correct_text = ""
        correct_letter = ""
        for opt in options:
            opt_str = str(opt)
            if opt_str.upper().startswith(correct_opt.upper() + ")"):
                correct_letter = opt_str[0].upper()
                correct_text = opt_str[3:] if len(opt_str) > 3 else ""
                break
        
        # If no matching option found, use the first option as fallback
        if not correct_letter and options:
            correct_letter = str(options[0])[0].upper() if options else ""
        
        # Get user's answer
        user_ans = str(user_ans).strip().upper() if user_ans else ""
        user_letter = user_ans[0] if user_ans else ""
        
        # Check if answer is correct (case-insensitive first letter match)
        is_correct = user_letter == correct_letter
        if is_correct:
            total_score += question_marks
            correct_answers += 1
        
        # Prepare feedback
        feedback = {
            "question": question_text,
            "user_answer": user_ans,
            "correct_answer": f"{correct_letter}) {correct_text}" if correct_letter else "No correct answer provided",
            "is_correct": is_correct,
            "marks_awarded": question_marks if is_correct else 0,
            "max_marks": question_marks,
            "explanation": q.get("explanation", "No explanation provided.") # Extract explanation here
        }
        
        feedback_list.append(feedback)
        
        # Track incorrect questions for suggestions
        if not is_correct:
            incorrect_questions.append({
                "question": question_text,
                "user_answer": user_ans,
                "correct_answer": f"{correct_letter}) {correct_text}",
                "topic": q.get("topic", "General"),
                "difficulty": q.get("difficulty", "Medium")
            })
    
    # Calculate percentage score
    percentage = (total_score / max_score * 100) if max_score > 0 else 0
    
    # Generate suggestions based on performance
    if incorrect_questions:
        # Group incorrect questions by topic
        topics = {}
        for q in incorrect_questions:
            topic = q.get("topic", "General")
            if topic not in topics:
                topics[topic] = 0
            topics[topic] += 1
        
        # Generate personalized suggestions
        suggestions = [
            f"You scored {correct_answers} out of {len(quiz_data)} questions correctly.",
            f"Total score: {total_score}/{max_score} ({percentage:.1f}%)"
        ]
        
        if topics:
            suggestions.append("\nAreas to focus on:")
            for topic, count in topics.items():
                suggestions.append(f"- {topic}: {count} incorrect answer{'s' if count > 1 else ''}")
        
        suggestions.extend([
            "\nTips for improvement:",
            "- Review the explanations for incorrect answers",
            "- Practice more questions on the topics you struggled with",
            "- Take notes on key concepts you found challenging"
        ])
    else:
        suggestions = [
            f"🎉 Perfect score! You got all {len(quiz_data)} questions right!",
            f"Total score: {total_score}/{max_score} (100%)",
            "\nGreat job! You've mastered this material.",
            "Consider trying a more challenging quiz next time!"
        ]
    
    # Prepare the result dictionary
    result = {
        "status": "success",
        "total_score": total_score,
        "max_score": max_score,
        "percentage": round(percentage, 2),
        "feedback": feedback_list,
        "suggestions": suggestions,
        "correct_answers": correct_answers,
        "total_questions": len(quiz_data)
    }
    
    # Add debug information
    print("\n=== Evaluation Results ===")
    print(f"Total Score: {total_score}/{max_score} ({percentage:.1f}%)")
    print(f"Correct Answers: {correct_answers}/{len(quiz_data)}")
    print(f"Suggestions: {len(suggestions)}")
    
    return result


# ----------------------------
# 🔹 3. Hint generation for a question
# ----------------------------
def generate_hint_ai(question_text: str, user_answer: Optional[str] = None) -> str:
    """
    Generate a helpful hint for the given question using AI.
    
    Args:
        question_text: The question to generate a hint for
        user_answer: Optional user's current answer to provide more targeted hints
        
    Returns:
        A helpful hint or guidance for the question
        
    Raises:
        Exception: If there's an error generating the hint
    """
    # Input validation
    if not question_text or not isinstance(question_text, str) or not question_text.strip():
        return "Please provide a valid question."
        
    # Simple fallback hints based on question type
    fallback_hints = [
        "Try breaking the problem down into smaller steps.",
        "Review the key concepts related to this question.",
        "Check if you've considered all the given information.",
        "Try to eliminate obviously wrong answers first.",
        "Think about any formulas or concepts that might apply here.",
        "Make sure you understand all the terms in the question.",
        "Try to rephrase the question in your own words.",
        "Consider drawing a diagram to visualize the problem.",
        "Think about similar problems you've solved before.",
        "Check your calculations carefully."
    ]
    
    try:
        # Build the prompt based on whether we have a user answer or not
        if user_answer and user_answer.strip():
            prompt = f"""
            You are an expert teacher helping a student with a quiz question.
            The student has provided an answer but might need some guidance.
            
            Question: "{question_text}"
            Student's Answer: "{user_answer}"
            
            Please provide a helpful hint that will guide the student toward the correct answer 
            without giving it away. Consider their current answer in your response.
            The hint should:
            1. Acknowledge what's correct in their answer (if anything)
            2. Gently point out any misconceptions
            3. Suggest a strategy or concept to consider
            4. Be encouraging and constructive
            5. Be concise (1-2 sentences)
            6. Never reveal the final answer
            
            If you cannot provide a specific hint, just say: "I'm not sure how to help with this question."
            """
        else:
            prompt = f"""
            You are an expert teacher helping a student with a quiz question.
            
            Question: "{question_text}"
            
            Please provide a helpful hint that will guide the student toward the answer 
            without giving it away. The hint should:
            1. Point to key concepts or strategies
            2. Break down complex problems into simpler steps
            3. Suggest relevant formulas or concepts to consider
            4. Be concise (1-2 sentences)
            5. Not reveal the final answer
            
            If you cannot provide a specific hint, just say: "I'm not sure how to help with this question."
            """
        
        try:
            # Generate the hint using the AI model with a timeout
            response = model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "top_k": 40,
                    "max_output_tokens": 150,
                },
                # safety_settings={
                #     "HARASSMENT": "block_none",
                #     "HATE_SPEECH": "block_none",
                #     "SEXUALLY_EXPLICIT": "block_none",
                #     "DANGEROUS_CONTENT": "block_none"
                # }
            )
            
            if not response or not hasattr(response, 'text') or not response.text:
                raise ValueError("Empty or invalid response from AI model")
                
            # Clean up the response
            hint = response.text.strip()
            
            # Check for common error messages
            if any(error in hint.lower() for error in ["error", "sorry", "i can't", "i don't", "i'm not"]):
                raise ValueError("AI returned an error message")
            
            # Remove any markdown formatting, quotes, or unwanted prefixes
            for prefix in ["hint:", "suggestion:", "\"", "'"]:
                if hint.lower().startswith(prefix):
                    hint = hint[len(prefix):].strip()
            hint = hint.strip('\"\'')
            
            # Ensure the hint is a reasonable length
            if len(hint) > 250:
                hint = hint[:247] + '...'
            elif not hint or len(hint) < 10:  # If too short, it's probably not helpful
                raise ValueError("Hint too short or empty")
                
            return hint
            
        except Exception as ai_error:
            print(f"AI generation failed, using fallback hint: {str(ai_error)}")
            # Return a random fallback hint
            import random
            return random.choice(fallback_hints)
        
    except Exception as e:
        print(f"Error in generate_hint_ai: {str(e)}")
        # Return a fallback hint if there's any error
        import random
        return random.choice(fallback_hints)


# ----------------------------
# 🔹 4. Adaptive difficulty suggestion
# ----------------------------
def suggest_difficulty_ai(previous_score):
    """
    Adjust next quiz difficulty based on previous performance.
    """
    if previous_score >= 80:
        return "HARD"
    elif previous_score >= 50:
        return "MEDIUM"
    else:
        return "EASY"