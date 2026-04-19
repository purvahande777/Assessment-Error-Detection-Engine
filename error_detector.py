import json
import logging
from datetime import datetime

# ---------------------------------------------------------
# Step 1: Setup the System Logger
# This will automatically create an "assessment_errors.log" file
# ---------------------------------------------------------
logging.basicConfig(
    filename='assessment_errors.log',
    level=logging.ERROR,
    format='%(asctime)s - [%(levelname)s] - %(message)s'
)

class AssessmentErrorDetector:
    def __init__(self):
        self.errors_found = []

    def log_error(self, category, message):
        """Logs the error to the file and stores it in the memory list."""
        formatted_message = f"{category}: {message}"
        logging.error(formatted_message)
        self.errors_found.append({
            "timestamp": datetime.now().isoformat(),
            "category": category,
            "message": message
        })
        print(f"❌ ERROR DETECTED: {formatted_message}")

    def analyze_session(self, session_data):
        """Runs all checks on a candidate's assessment session."""
        candidate_id = session_data.get("candidate_id", "Unknown_Candidate")
        questions = session_data.get("questions", [])
        
        print(f"--- Analyzing Session for Candidate: {candidate_id} ---")

        # RULE 1: Check Total Questions Rule (Must be exactly 10)
        if len(questions) != 10:
            self.log_error("LOGICAL_ERROR", f"Candidate {candidate_id} was served {len(questions)} questions instead of exactly 10.")

        for index, q in enumerate(questions):
            q_id = q.get("question_id", f"Unknown_{index}")
            
            # RULE 2: Check First Question Rule (Must be Introduction)
            if index == 0 and q.get("type") != "Introduction":
                self.log_error("LOGICAL_ERROR", f"Question 1 is not an Introduction. (Found type: '{q.get('type')}')")
            
            # RULE 3: Check Time Limit Rule (Max 1800 seconds / 30 mins)
            time_spent = q.get("time_spent_seconds", 0)
            if time_spent > 1800:
                self.log_error("LOGICAL_ERROR", f"Exceeded 30-minute time limit on Q{q_id} ({time_spent} seconds recorded).")

            # RULE 4: Check Negative Marking Rule (Must be exactly -0.25)
            is_correct = q.get("is_correct")
            score_awarded = q.get("score_awarded", 0)
            if is_correct is False and score_awarded != -0.25:
                self.log_error("LOGICAL_ERROR", f"Incorrect negative marking on Q{q_id}. Awarded {score_awarded} instead of -0.25.")

            # RULE 5: Check System-Level Errors (Face Detection & Multiple Persons)
            face_status = q.get("faces_detected")
            if face_status is None or face_status == "null":
                self.log_error("SYSTEM_ERROR", f"Face detection API signal lost during Q{q_id}.")
            elif isinstance(face_status, int) and face_status > 1:
                self.log_error("SECURITY_ALERT", f"Multiple persons ({face_status}) detected in camera frame during Q{q_id}.")

            # RULE 6: Check LLM Evaluation Failure (Must be a number)
            llm_score = q.get("llm_evaluated_score")
            if not isinstance(llm_score, (int, float)):
                self.log_error("SYSTEM_ERROR", f"LLM returned invalid score format on Q{q_id}. (Received string/null instead of number).")

        return self.errors_found


# ---------------------------------------------------------
# Step 3: Run Fake Data to Generate the Deliverable Logs
# ---------------------------------------------------------
if __name__ == "__main__":
    # This is a "broken" test session to prove our detector works
    mock_bad_session = {
        "candidate_id": "CAND-9942",
        "domain": "Data Science",
        "questions": [
            # Q1: Fails the Introduction rule and Face Detection fails
            {"question_id": "1", "type": "Technical", "time_spent_seconds": 120, "is_correct": True, "score_awarded": 1.0, "faces_detected": "null", "llm_evaluated_score": 1.0},
            
            # Q2: Fails the Negative Marking rule (gave 0 instead of -0.25)
            {"question_id": "2", "type": "Technical", "time_spent_seconds": 300, "is_correct": False, "score_awarded": 0.0, "faces_detected": 1, "llm_evaluated_score": 0.0},
            
            # Q3: Fails the Time Limit rule (spent 40 minutes)
            {"question_id": "3", "type": "Technical", "time_spent_seconds": 2400, "is_correct": True, "score_awarded": 1.0, "faces_detected": 1, "llm_evaluated_score": 1.0},
            
            # Q4: Triggers a Security Alert (Multiple faces) & LLM returns text instead of number
            {"question_id": "4", "type": "Technical", "time_spent_seconds": 150, "is_correct": False, "score_awarded": -0.25, "faces_detected": 2, "llm_evaluated_score": "Error: Timeout"}
        ]
        # Notice we only gave 4 questions instead of 10. This will trigger the Total Questions rule!
    }

    detector = AssessmentErrorDetector()
    results = detector.analyze_session(mock_bad_session)
    
    print("\n✅ Scan Complete. Error log file generated successfully.")