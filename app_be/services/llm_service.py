# type: ignore
import json
import os
from typing import Any, Optional

from dotenv import load_dotenv
from json_repair import repair_json
from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.providers.anthropic import AnthropicProvider

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


def generate_questions_from_content(
    topic_name: str,
    topic_description: str,
    contents: list[dict[str, Any]],
    difficulty: Optional[DifficultyLevel] = None,
    question_count: int = 3,
    question_type: QuestionType = QuestionType.multiple_choice,
    retries: int = 1,
) -> list[dict[str, Any]]:
    """Generate quiz questions using LLM based on topic content"""
    if retries:
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

        # Create the prompt for the LLM
        prompt = f"""
    You are an expert linear algebra instructor.
    Create {question_count} {difficulty_text} {question_type} questions
    On the topic: "{topic_name}".
    Topic description: {topic_description}

    Here is the content material for this topic:

    {formatted_content}

    For each question:
    1. Create a clear, concise question text.
    2. For multiple choice questions, provide exactly 4 answer options with
    ONE correct answer and THREE plausible distractors.
    3. Include LaTeX where appropriate for mathematical notation.
    4. Explain why the correct answer is correct and why each incorrect answer is wrong.
    5. Assign the appropriate difficulty level (easy, medium, or hard).

    Format your response as a JSON array of question objects,
    where each object has the following structure:
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
    """

        # Call the LLM API
        try:
            response = call_llm_api(prompt)

            # Extract and parse the JSON response
            questions = extract_questions_from_llm_response(response)

            try:
                parsed_questions = json.loads(questions)
            except json.JSONDecodeError:
                repaired_questions = repair_json(questions)
                parsed_questions = json.loads(repaired_questions)

            # Validate the response
            validated_questions = []
            for q in parsed_questions:
                # Ensure required fields exist
                if all(
                    key in q
                    for key in ["text", "question_type", "difficulty", "answers"]
                ):
                    # Validate answers
                    if q["question_type"] == QuestionType.multiple_choice:
                        # Ensure there are at least 4 answers with one correct answer
                        if (
                            len(q["answers"]) >= 4
                            and sum(a.get("is_correct", False) for a in q["answers"])
                            == 1
                        ):
                            validated_questions.append(q)

            return validated_questions

        except Exception as e:
            print(f"Error generating questions: {str(e)}")
            # Return a backup set of generic questions if LLM generation fails
            retry_counter = retries - 1
            return generate_questions_from_content(
                topic_name, difficulty, question_count, retries=retry_counter
            )
    else:
        print("Error generating questions: Max retries exceeded")
        return []


def extract_questions_from_llm_response(response: str) -> list[dict[str, Any]]:
    """Extract and parse the JSON questions from the LLM response"""
    try:
        # Find JSON in the response (might be wrapped in markdown code blocks)
        json_start = response.find("[")
        json_end = response.rfind("]") + 1

        if json_start >= 0 and json_end > json_start:
            json_str = response[json_start:json_end]
            return json.loads(json_str)

        # Alternative approach: look for JSON wrapped in code blocks
        import re

        json_match = re.search(
            r"```(?:json)?\s*(\[\s*\{.*?\}\s*\])\s*```", response, re.DOTALL
        )
        if json_match:
            return json.loads(json_match.group(1))

        raise Exception("Could not extract valid JSON from LLM response")

    except json.JSONDecodeError:
        raise Exception("Failed to parse JSON from LLM response")
