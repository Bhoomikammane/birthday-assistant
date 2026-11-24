import os
import json
import calendar
import re

from openai import OpenAI
from dotenv import load_dotenv

# Load API key from .env
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
model_name = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

client = OpenAI(api_key=api_key) if api_key else None


# Allowed intents
ALLOWED_INTENTS = {
    "birthday_search",
    "count_birthdays",
    "upcoming_birthdays",
    "person_place",
    "unknown"
}


# System instructions for AI
SYSTEM_PROMPT = """
You are an NLU parser for a Birthday Assistant.

Your job is ONLY to understand the user's question.
Do not answer the question.
Do not invent birthdays, names, dates or places.

Return valid JSON with exactly these keys:

{
    "intent": "birthday_search",
    "entities": {
        "person_name": null,
        "relationship": null,
        "month": null,
        "relative_date": null,
        "relative_month": null,
        "place": null
    }
}

Allowed intents:
- birthday_search
- count_birthdays
- upcoming_birthdays
- person_place
- unknown

Entity meanings:
- person_name: Name or nickname of a person.
- relationship: Relationship such as Nephew, Niece, Wife, Brother.
- month: Month name such as September or October.
- relative_date: Use "tomorrow" when the user asks about tomorrow.
- relative_month: Use "next" when the user asks about next month.
- place: A location mentioned in the question.

Important rules:
1. Always carefully check whether the user mentions a person's name.
2. If a person's name is mentioned, extract the complete name.
3. Do not ignore a person's name just because a relationship was mentioned earlier.
4. If the user asks for one person's birthday, use birthday_search.
5. If the user asks how many birthdays, use count_birthdays.
6. If the user asks about upcoming birthdays, use upcoming_birthdays.
7. If the user asks where someone lives, use person_place.
8. For birthday-related questions, use birthday_search.
9. Do not create names or relationships.
10. Return JSON only. Do not include explanations or markdown.
"""


# Normalize names and messages
def normalize_text(text):
    text = str(text).lower().strip()

    # Remove possessive apostrophes
    text = re.sub(r"['’]s\b", "", text)

    # Replace punctuation with spaces
    text = re.sub(r"[^a-z0-9\s]", " ", text)

    # Remove extra spaces
    text = " ".join(text.split())

    return text


# Find a person's name directly in the user's message
def find_person_in_message(message, people):

    normalized_message = normalize_text(message)

    matches = []

    for _, row in people.iterrows():

        name = str(row["Name"]).strip()

        if not name or name.lower() == "nan":
            continue

        aliases = [name]

        nickname = row.get("Nickname")

        if nickname is not None and str(nickname).lower() != "nan":
            aliases.append(str(nickname).strip())

        for alias in aliases:

            normalized_alias = normalize_text(alias)

            if not normalized_alias:
                continue

            # Match complete name or nickname.
            # Also supports possessive wording such as "Varun Kumar's".
            pattern = (
                r"(?<!\w)"
                + re.escape(normalized_alias).replace(r"\ ", r"\s+")
                + r"(?:s)?"
                + r"(?!\w)"
            )

            if re.search(pattern, normalized_message):
                matches.append(row)
                break

    # Remove duplicate Person_ID matches
    unique_matches = {}

    for row in matches:
        unique_matches[row["Person_ID"]] = row

    return list(unique_matches.values())


def parse_with_llm(message, people):

    if client is None:
        raise ValueError("OpenAI API key is missing.")

    # First check Excel for an explicitly mentioned person.
    # This prevents the previous relationship context from
    # overriding a clearly mentioned person's name.
    direct_person_matches = find_person_in_message(message, people)

    # Send question to the LLM
    response = client.responses.create(
        model=model_name,
        input=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": message
            }
        ],
        text={
            "format": {
                "type": "json_object"
            }
        }
    )

    # Extract JSON response
    result = json.loads(response.output_text)

    intent = result.get("intent", "unknown")
    entities = result.get("entities", {})

    if intent not in ALLOWED_INTENTS:
        raise ValueError("Invalid intent returned by LLM.")

    if not isinstance(entities, dict):
        raise ValueError("Invalid entities returned by LLM.")

    # Normalize entities
    entities = {
        "person_name": entities.get("person_name"),
        "relationship": entities.get("relationship"),
        "month": entities.get("month"),
        "relative_date": entities.get("relative_date"),
        "relative_month": entities.get("relative_month"),
        "place": entities.get("place")
    }

    # Convert month name into month number
    month = entities.get("month")

    if month:
        month = str(month).strip().capitalize()

        if month not in calendar.month_name:
            raise ValueError("Invalid month returned by LLM.")

        entities["month"] = list(calendar.month_name).index(month)

    # Validate relationship against Excel data
    relationship = entities.get("relationship")

    if relationship:

        relationships = (
            people["Relationship"]
            .dropna()
            .astype(str)
            .str.strip()
            .tolist()
        )

        matching_relationship = next(
            (
                r for r in relationships
                if r.lower() == str(relationship).strip().lower()
            ),
            None
        )

        if matching_relationship is None:
            raise ValueError("Unknown relationship returned by LLM.")

        entities["relationship"] = matching_relationship

    # PRIORITY 1: Use a person explicitly found in the message
    if len(direct_person_matches) == 1:

        person = direct_person_matches[0]

        entities["person_id"] = person["Person_ID"]
        entities["person_name"] = person["Name"]

        # A specific person's name takes priority over an old
        # relationship context in the conversation.

    elif len(direct_person_matches) > 1:

        raise ValueError("Multiple matching people found. Clarification required.")

    else:

        # PRIORITY 2: Validate the name extracted by the LLM
        person_name = entities.get("person_name")

        if person_name:

            search_name = normalize_text(person_name)

            matched_person = people[
                (
                    people["Name"]
                    .fillna("")
                    .astype(str)
                    .apply(normalize_text)
                    == search_name
                )
                |
                (
                    people["Nickname"]
                    .fillna("")
                    .astype(str)
                    .apply(normalize_text)
                    == search_name
                )
            ]

            if len(matched_person) == 1:

                person = matched_person.iloc[0]

                entities["person_id"] = person["Person_ID"]
                entities["person_name"] = person["Name"]

            elif matched_person.empty:

                raise ValueError("Person not found in Excel dataset.")

            else:

                raise ValueError("Ambiguous person name.")

    return {
        "intent": intent,
        "entities": entities
    }