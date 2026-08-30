# lesson_engine.py
# Pre-loaded NIPUN Bharat FLN lesson templates for Grades 1-3
# Turns VaaniSetu from a translation tool into a teaching assistant

import time

# Each lesson has: introduction, 3 teaching steps, assessment prompts,
# expected student responses, and a comprehension check

NIPUN_LESSONS = {
    "grade1": {
        "counting_1_10": {
            "title": "Counting 1 to 10",
            "competency": "Counts objects up to 10 and says numbers in order",
            "steps": [
                {
                    "type": "lesson_script",
                    "hindi": "आज हम एक से दस तक गिनना सीखेंगे।",
                    "note": "Introduction — show fingers"
                },
                {
                    "type": "activity_instruction",
                    "hindi": "अपनी उंगलियां दिखाओ और मेरे साथ गिनो। एक, दो, तीन...",
                    "note": "Activity — count with fingers"
                },
                {
                    "type": "activity_instruction",
                    "hindi": "अब तुम्हारे सामने पांच पत्थर हैं। उन्हें गिनो।",
                    "note": "Practice — count objects"
                },
                {
                    "type": "assessment_prompt",
                    "hindi": "यहाँ कितने पत्थर हैं? बताओ।",
                    "note": "Assessment — teacher holds up 3 stones",
                    "expected_count": 3,
                    "accept_range": [2, 4]
                },
            ]
        },
        "shapes": {
            "title": "Basic Shapes",
            "competency": "Identifies and names basic shapes",
            "steps": [
                {
                    "type": "lesson_script",
                    "hindi": "आज हम आकार सीखेंगे। यह गोल है।",
                    "note": "Show circle"
                },
                {
                    "type": "lesson_script",
                    "hindi": "यह चौकोर है। इसके चार कोने हैं।",
                    "note": "Show square"
                },
                {
                    "type": "activity_instruction",
                    "hindi": "अपने आसपास गोल चीज़ें ढूंढो।",
                    "note": "Find circular objects"
                },
                {
                    "type": "assessment_prompt",
                    "hindi": "यह कौन सा आकार है?",
                    "note": "Point to a shape on board"
                }
            ]
        }
    },
    "grade2": {
        "addition": {
            "title": "Simple Addition",
            "competency": "Adds single-digit numbers with objects",
            "steps": [
                {
                    "type": "lesson_script",
                    "hindi": "आज हम जोड़ना सीखेंगे। एक और एक मिलाओ।",
                    "note": "Introduction to addition"
                },
                {
                    "type": "activity_instruction",
                    "hindi": "दो आम और तीन आम — कुल कितने आम हुए? अपनी उंगलियों पर गिनो।",
                    "note": "Use objects to add"
                },
                {
                    "type": "activity_instruction",
                    "hindi": "अब तुम एक सवाल बनाओ। पांच और कितने जोड़ोगे?",
                    "note": "Student creates own problem"
                },
                {
                    "type": "assessment_prompt",
                    "hindi": "तीन और चार कितने होते हैं?",
                    "note": "Oral assessment",
                    "correct_answer": "7",
                    "accept_answers": ["7", "सात"]
                }
            ]
        },
        "reading_words": {
            "title": "Reading Simple Words",
            "competency": "Reads common two-syllable words",
            "steps": [
                {
                    "type": "lesson_script",
                    "hindi": "यह शब्द है — 'माँ'। इसे पढ़ो।",
                    "note": "Show word card"
                },
                {
                    "type": "activity_instruction",
                    "hindi": "इस शब्द को तीन बार पढ़ो — 'पानी'।",
                    "note": "Repetition practice"
                },
                {
                    "type": "assessment_prompt",
                    "hindi": "यह शब्द क्या है? पढ़कर बताओ।",
                    "note": "Hold up word card"
                }
            ]
        }
    },
    "grade3": {
        "subtraction": {
            "title": "Simple Subtraction",
            "competency": "Subtracts single-digit numbers",
            "steps": [
                {
                    "type": "lesson_script",
                    "hindi": "आज हम घटाना सीखेंगे। दस में से तीन घटाओ।",
                    "note": "Introduction to subtraction"
                },
                {
                    "type": "activity_instruction",
                    "hindi": "सात पत्थर लो। तीन हटा दो। अब कितने बचे?",
                    "note": "Concrete subtraction"
                },
                {
                    "type": "assessment_prompt",
                    "hindi": "आठ में से पांच घटाओ। उत्तर क्या है?",
                    "note": "Oral assessment",
                    "correct_answer": "3",
                    "accept_answers": ["3", "तीन"]
                }
            ]
        }
    }
}


def get_lesson(grade, topic):
    """Returns lesson object or None"""
    grade_key = f"grade{grade}"
    return NIPUN_LESSONS.get(grade_key, {}).get(topic)


def get_all_lessons():
    """Returns flat list of all available lessons for UI display"""
    lessons = []
    for grade_key, topics in NIPUN_LESSONS.items():
        grade_num = grade_key.replace("grade", "")
        for topic_key, lesson in topics.items():
            lessons.append({
                "grade": grade_num,
                "topic": topic_key,
                "title": lesson["title"],
                "competency": lesson["competency"],
                "step_count": len(lesson["steps"])
            })
    return lessons


class LessonSession:
    """
    Tracks a live lesson session.
    Records teacher translations, student responses, and generates
    comprehension score at the end — the teacher's session summary.
    """

    def __init__(self, lesson):
        self.lesson = lesson
        self.current_step = 0
        self.total_steps = len(lesson["steps"])
        self.translations = []
        self.student_responses = []
        self.start_time = time.time()

    def current_step_data(self):
        if self.current_step >= self.total_steps:
            return None
        return self.lesson["steps"][self.current_step]

    def record_translation(self, hindi, santali, latency):
        self.translations.append({
            "step": self.current_step,
            "hindi": hindi,
            "santali": santali,
            "latency": latency
        })

    def advance_step(self):
        self.current_step = min(self.current_step + 1, self.total_steps)

    def record_student_response(self, response_text):
        """
        Record student response and compute comprehension signal.
        Returns: "green" | "yellow" | "red"
        """
        step = self.lesson["steps"][self.current_step - 1]

        signal = "yellow"

        if "accept_answers" in step:
            response_clean = response_text.strip().lower()
            correct = [a.lower() for a in step["accept_answers"]]
            if response_clean in correct:
                signal = "green"
            elif len(response_clean) > 0:
                signal = "yellow"
            else:
                signal = "red"

        elif "accept_range" in step:
            try:
                num = int(''.join(filter(str.isdigit, response_text)))
                lo, hi = step["accept_range"]
                signal = "green" if lo <= num <= hi else "red"
            except:
                signal = "yellow"

        self.student_responses.append({
            "step": self.current_step - 1,
            "response": response_text,
            "signal": signal
        })
        return signal

    def get_session_summary(self):
        """
        Returns teacher-facing session summary after lesson completes.
        """
        duration = round(time.time() - self.start_time)
        minutes = duration // 60
        seconds = duration % 60

        green  = sum(1 for r in self.student_responses if r["signal"] == "green")
        yellow = sum(1 for r in self.student_responses if r["signal"] == "yellow")
        red    = sum(1 for r in self.student_responses if r["signal"] == "red")
        total  = len(self.student_responses)

        if total == 0:
            comprehension = "No assessment responses recorded"
            score_pct = 0
        else:
            score_pct = round((green / total) * 100)
            if score_pct >= 70:
                comprehension = "Good — students understood the lesson"
            elif score_pct >= 40:
                comprehension = "Partial — repeat key concepts next session"
            else:
                comprehension = "Needs reinforcement — revisit this lesson"

        avg_latency = (
            round(sum(t["latency"] for t in self.translations) / len(self.translations), 2)
            if self.translations else 0
        )

        return {
            "lesson_title": self.lesson["title"],
            "competency": self.lesson["competency"],
            "duration": f"{minutes}m {seconds}s",
            "steps_completed": self.current_step,
            "total_steps": self.total_steps,
            "sentences_translated": len(self.translations),
            "avg_translation_latency": avg_latency,
            "comprehension": {
                "green": green,
                "yellow": yellow,
                "red": red,
                "score_percent": score_pct,
                "summary": comprehension
            }
        }