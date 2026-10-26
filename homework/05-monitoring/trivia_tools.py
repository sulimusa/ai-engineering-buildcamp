import html
import json
import urllib.parse
import urllib.request

from pydantic_ai import ModelRetry

BASE_URL = "https://opentdb.com"


def _get_json(url: str) -> dict:
    # Download a URL and parse the JSON text into a dictionary.
    with urllib.request.urlopen(url, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


# Group the two trivia tools in a class, like SearchTools and SQLTools.
class TriviaTools:
    # The docstring and type hints are what the model sees as this tool's description.
    def get_categories(self) -> list[dict]:
        """List the trivia categories as {id, name}. Use an id when fetching questions."""
        data = _get_json(f"{BASE_URL}/api_category.php")
        return data["trivia_categories"]

    def get_questions(self, amount: int = 5, category: int | None = None, difficulty: str | None = None) -> list[dict]:
        """Fetch multiple-choice trivia questions.

        amount: how many questions (1-10).
        category: optional category id from get_categories.
        difficulty: optional, one of easy, medium, hard.
        """
        params = {"amount": max(1, min(amount, 10)), "type": "multiple"}
        if category is not None:
            params["category"] = category
        if difficulty is not None:
            params["difficulty"] = difficulty
        data = _get_json(f"{BASE_URL}/api.php?{urllib.parse.urlencode(params)}")
        # response_code 0 means success; anything else is a problem the model can react to.
        if data["response_code"] != 0:
            raise ModelRetry(f"Trivia API returned code {data['response_code']} (1 = not enough questions, 5 = too many requests). Adjust and retry.")
        # The API returns HTML entities such as &quot; in the text, so unescape them.
        return [
            {
                "category": item["category"],
                "difficulty": item["difficulty"],
                "question": html.unescape(item["question"]),
                "correct_answer": html.unescape(item["correct_answer"]),
                "incorrect_answers": [html.unescape(a) for a in item["incorrect_answers"]],
            }
            for item in data["results"]
        ]
