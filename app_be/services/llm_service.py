# type: ignore
import json
import os
from typing import Any, Optional

from dotenv import load_dotenv
from json_repair import repair_json
from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.providers.anthropic import AnthropicProvider
from tenacity import retry, stop_after_attempt, wait_fixed

from app_be.models.schemas import DifficultyLevel, QuestionType

load_dotenv()
LLM_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL_TEST")


def call_llm_api(prompt: str) -> str:
    """Call the Anthropic LLM using the pydantic_ai agent."""
    model = AnthropicModel(
        ANTHROPIC_MODEL, provider=AnthropicProvider(api_key=LLM_API_KEY)
    )
    agent = Agent(model)
    response = agent.run_sync(prompt)
    print(response.output)
    return response.output


@retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
def call_llm_api_with_retry(prompt: str) -> str:
    """Call LLM API with retry logic built in"""
    return call_llm_api(prompt)  # Assuming this function exists elsewhere


def extract_json_from_response(response: str) -> list[dict[str, Any]]:
    """Extract and parse JSON from LLM response with better error handling"""
    try:
        # First try to parse the entire response as JSON
        return json.loads(response)
    except json.JSONDecodeError:
        # Try to repair the JSON
        try:
            repaired = repair_json(response)
            return json.loads(repaired)
        except Exception:
            # If that fails, look for JSON array in the response
            import re

            json_pattern = r"\[\s*\{.*\}\s*\]"
            match = re.search(json_pattern, response, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except json.JSONDecodeError:
                    repaired = repair_json(match.group(0))
                    return json.loads(repaired)

            # If still fails, try to find individual JSON objects
            questions = []
            pattern = r"\{(?:[^{}]|(?:\{[^{}]*\}))*\}"
            matches = re.finditer(pattern, response)
            for match in matches:
                try:
                    question = json.loads(match.group(0))
                    questions.append(question)
                except json.JSONDecodeError as e:
                    print(f"Error parsing question JSON: {e}")
                except Exception as e:
                    print(f"Unexpected error parsing question: {e}")

            if questions:
                return questions

            raise ValueError("Failed to extract valid JSON from response")


def validate_question(question: dict[str, Any], question_type: str) -> bool:
    """Validate a single question based on criteria"""
    # Check required fields
    required_fields = ["text", "question_type", "difficulty", "answers"]
    if not all(field in question for field in required_fields):
        return False

    # Validate answers based on question type
    if question["question_type"] == QuestionType.multiple_choice:
        answers = question.get("answers", [])
        # Check if there are at least 4 answers
        if len(answers) < 4:
            return False
        # Check if exactly one answer is marked correct
        correct_count = sum(1 for a in answers if a.get("is_correct", False))
        if correct_count != 1:
            return False

    return True


def generate_questions_from_content(
    topic_name: str,
    topic_description: str,
    contents: list[dict[str, Any]],
    difficulty: Optional[DifficultyLevel] = None,
    question_count: int = 3,
    question_type: str = QuestionType.multiple_choice,
    retries: int = 3,
) -> list[dict[str, Any]]:
    """Generate quiz questions using LLM based on topic content"""
    # Format the content for the LLM prompt
    formatted_content = ""
    for content in contents:
        content_type = content.get("content_type", "")
        title = content.get("title", "")
        text = content.get("text_content", "")
        latex = content.get("latex_content", "")

        formatted_content += f"--- {content_type.upper()}: {title} ---\n"
        formatted_content += f"{text}\n"
        if latex:
            formatted_content += f"LaTeX: {latex}\n"
        formatted_content += "\n"

    # Determine difficulty level for prompt
    difficulty_text = ""
    if difficulty:
        difficulty_text = f"at {difficulty} difficulty level"

    # Prefill the expected JSON structure
    json_prefill = """[
  {
    "text": """

    # Create the prompt for the LLM
    prompt = f"""
You are an expert linear algebra instructor.
Create {question_count} {question_type} questions {difficulty_text}.
Topic name: {topic_name}
Here is the content material for this topic:
{formatted_content}
For each question:
1. Create a clear, concise question text.
2. For multiple choice questions, provide exactly 4 answer options
3. There should be ONE correct answer and THREE plausible distractors.
4. Include LaTeX where appropriate for mathematical notation.
5. Explain why the correct answer is correct and why each incorrect answer is wrong.
6. Assign the appropriate difficulty level (easy, medium, or hard).
Format your response as a JSON array of question objects.
Each object MUST have the following structure:
{{
  "text": "Question text",
  "latex_content": "LaTeX representation (if needed)",
  "question_type": "{question_type}",
  "difficulty": "easy|medium|hard",
  "answers": [
    {{
      "text": "Answer option text",
      "latex_content": "LaTeX representation (if needed)",
      "is_correct": true|false,
      "explanation": "Explanation why this answer is correct/incorrect"
    }},
    ...more answers...
  ]
}}

IMPORTANT: Make sure the JSON is valid and properly formatted.
Start your response with {json_prefill}
"""

    # Implement retry logic with tenacity
    try:
        # Call the LLM API with built-in retries
        response = call_llm_api_with_retry(prompt)

        # Extract and parse the JSON response
        questions = extract_json_from_response(response)

        # Make sure questions is a list
        if not isinstance(questions, list):
            questions = [questions]

        # Validate each question
        validated_questions = []
        for question in questions:
            if validate_question(question, question_type):
                validated_questions.append(question)

        if not validated_questions and retries > 0:
            # If no valid questions, retry with one fewer retry
            return generate_questions_from_content(
                topic_name=topic_name,
                topic_description=topic_description,
                contents=contents,
                difficulty=difficulty,
                question_count=question_count,
                question_type=question_type,
                retries=retries - 1,
            )

        return validated_questions

    except Exception as e:
        print(f"Error generating questions: {str(e)}")
        if retries > 0:
            # Retry with one fewer retry
            return generate_questions_from_content(
                topic_name=topic_name,
                topic_description=topic_description,
                contents=contents,
                difficulty=difficulty,
                question_count=question_count,
                question_type=question_type,
                retries=retries - 1,
            )
        else:
            print("Error generating questions: Max retries exceeded")
            return []
