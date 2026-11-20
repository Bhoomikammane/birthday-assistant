from flask import Flask, render_template, request, jsonify
import pandas as pd
from datetime import date, timedelta
import calendar
import re

app = Flask(__name__)

# Load Excel dataset
df = pd.read_excel("data/people.xlsx")

# Convert DOB into datetime format
df["DOB"] = pd.to_datetime(df["DOB"], errors="coerce")

# Remove rows with invalid dates
df = df.dropna(subset=["DOB"])

# Month dictionary
MONTHS = {
    month.lower(): number
    for number, month in enumerate(calendar.month_name)
    if month
}


# Calculate the next birthday
def next_birthday(dob, today):

    year = today.year

    try:
        candidate = date(year, dob.month, dob.day)
    except ValueError:
        candidate = date(year, 2, 28)

    if candidate < today:

        try:
            candidate = date(year + 1, dob.month, dob.day)
        except ValueError:
            candidate = date(year + 1, 2, 28)

    return candidate


# Format matching people
def fmt_people(rows):

    if rows.empty:
        return "No matching birthdays found."

    parts = []

    for _, row in rows.iterrows():

        parts.append(
            f"{row['Name']} - "
            f"{row['DOB'].strftime('%d %B')} "
            f"({row['Relationship']})"
        )

    return "\n".join(parts)


# Main chatbot logic
def answer(q):

    text = q.lower().strip()
    today = date.today()

    if not text:
        return "Please enter a question."

    work = df.copy()

    # 1. Search for a person's name or nickname
    for _, row in df.iterrows():

        names = [
            str(row["Name"]).lower(),
            str(row.get("Nickname", "")).lower()
        ]

        for name in names:

            if name and name != "nan":

                if re.search(
                    r"\b" + re.escape(name) + r"\b",
                    text
                ):

                    return (
                        f"{row['Name']}'s birthday is "
                        f"{row['DOB'].strftime('%d %B %Y')}."
                    )

    # 2. Relationship filtering
    for rel in sorted(
        df["Relationship"].dropna().unique(),
        key=len,
        reverse=True
    ):

        relationship = str(rel).lower()

        if (
            relationship in text
            or relationship + "s" in text
        ):

            work = work[
                work["Relationship"].str.lower() == relationship
            ]

            break

    # 3. Birthday tomorrow
    if "tomorrow" in text:

        target = today + timedelta(days=1)

        result = work[
            (work["DOB"].dt.month == target.month) &
            (work["DOB"].dt.day == target.day)
        ]

        return fmt_people(result)

    # 4. Find month in question
    month = None

    for name, number in MONTHS.items():

        if re.search(r"\b" + name + r"\b", text):

            month = number
            break

    # 5. Next month
    if "next month" in text:

        month = 1 if today.month == 12 else today.month + 1

    if month:

        result = work[
            work["DOB"].dt.month == month
        ]

        # Birthday count
        if "how many" in text or "count" in text:

            return (
                f"There are {len(result)} birthdays "
                f"in {calendar.month_name[month]}."
            )

        return fmt_people(result.sort_values("DOB"))

    # 6. Upcoming birthdays
    if "upcoming" in text or "next 30" in text:

        items = []

        for index, row in work.iterrows():

            birthday = next_birthday(
                row["DOB"].date(),
                today
            )

            difference = (birthday - today).days

            if 0 <= difference <= 30:

                items.append((difference, index))

        if not items:

            return "No birthdays in the next 30 days."

        ids = [
            index
            for difference, index in sorted(items)
        ]

        return fmt_people(work.loc[ids])

    # 7. Wife birthday
    if "wife" in text:

        result = df[
            df["Relationship"].str.lower() == "wife"
        ]

        return fmt_people(result)

    # 8. Location queries
    if "where" in text or "stay" in text or "live" in text:

        for _, row in df.iterrows():

            if str(row["Name"]).lower() in text:

                return (
                    f"{row['Name']} stays in "
                    f"{row['Place_of_Stay']}."
                )

    # 9. Default response
    return (
        "I understood this as a birthday query, "
        "but V1 supports only simple rules.\n\n"
        "Try asking:\n"
        "1. Upcoming birthdays\n"
        "2. Birthdays next month\n"
        "3. Birthday tomorrow\n"
        "4. Wife birthday\n"
        "5. Nephew birthdays in September\n"
        "6. When is Rahul Patil's birthday?"
    )


# Home page
@app.route("/")
def index():

    return render_template("index.html")


# Chat API
@app.route("/chat", methods=["POST"])
def chat():

    data = request.get_json()

    message = data.get("message", "")

    response = answer(message)

    return jsonify({
        "answer": response
    })


# Run Flask application
if __name__ == "__main__":

    app.run(debug=True)