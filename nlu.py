import calendar
import re

# Month dictionaryd
MONTHS = {
    month.lower(): number
    for number, month in enumerate(calendar.month_name)
    if month
}


def parse(message, people):

    text = message.lower().strip()

    result = {
        "intent": "unknown",
        "entities": {}
    }

    # -------------------------
    # 1. INTENT CLASSIFICATION
    # -------------------------

    if "how many" in text or "count" in text:
        result["intent"] = "count_birthdays"

    elif any(word in text for word in ["where", "stay", "live"]):
        result["intent"] = "person_place"

    elif any(word in text for word in ["upcoming", "next 30 days"]):
        result["intent"] = "upcoming_birthdays"

    elif any(word in text for word in [
        "birthday", "birthdays", "born", "celebration"
    ]):
        result["intent"] = "birthday_search"

    # -------------------------
    # 2. RELATIVE DATE
    # -------------------------

    if "tomorrow" in text:
        result["entities"]["relative_date"] = "tomorrow"

    # -------------------------
    # 3. RELATIVE MONTH
    # -------------------------

    if "next month" in text:
        result["entities"]["relative_month"] = "next"

    # -------------------------
    # 4. MONTH EXTRACTION
    # -------------------------

    for name, number in MONTHS.items():

        if re.search(r"\b" + name + r"\b", text):

            result["entities"]["month"] = number
            break

    # -------------------------
    # 5. RELATIONSHIP EXTRACTION
    # -------------------------

    if "Relationship" in people.columns:

        relationships = (
            people["Relationship"]
            .dropna()
            .unique()
        )

        for relationship in sorted(
            relationships,
            key=len,
            reverse=True
        ):

            token = str(relationship).lower()

            if (
                re.search(r"\b" + re.escape(token) + r"\b", text)
                or re.search(r"\b" + re.escape(token + "s") + r"\b", text)
            ):

                result["entities"]["relationship"] = relationship
                break

    # -------------------------
    # 6. PERSON NAME EXTRACTION
    # -------------------------

    for _, row in people.iterrows():

        candidates = [
            str(row["Name"]),
            str(row.get("Nickname", ""))
        ]

        for candidate in candidates:

            candidate = candidate.lower().strip()

            if (
                candidate
                and candidate != "nan"
                and re.search(
                    r"\b" + re.escape(candidate) + r"\b",
                    text
                )
            ):

                result["entities"]["person_id"] = row["Person_ID"]

                result["entities"]["person_name"] = row["Name"]

                break

        if "person_id" in result["entities"]:
            break

    return result