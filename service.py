from datetime import date, timedelta
import calendar


# -------------------------
# FORMAT BIRTHDAY RESULTS
# -------------------------

def format_rows(rows):

    if rows.empty:
        return "No matching people found. 🎂"

    return "\n".join(

        f"{row.Name} - {row.DOB.strftime('%d %B')} ({row.Relationship})"

        for _, row in rows.iterrows()

    )


# -------------------------
# EXECUTE USER QUERY
# -------------------------

def execute(parsed, df):

    intent = parsed["intent"]

    entities = parsed["entities"]

    work = df.copy()

    today = date.today()

    # -------------------------
    # PERSON SEARCH
    # -------------------------

    if "person_id" in entities:

        person = df[
            df["Person_ID"] == entities["person_id"]
        ]

        if person.empty:
            return "I couldn't find that person."

        row = person.iloc[0]

        if intent == "person_place":

            return f"{row.Name} stays in {row.Place_of_Stay}. 📍"

        return (
            f"{row.Name}'s birthday is "
            f"{row.DOB.strftime('%d %B %Y')}. 🎂"
        )

    # -------------------------
    # RELATIONSHIP FILTER
    # -------------------------

    if "relationship" in entities:

        work = work[
            work["Relationship"]
            .fillna("")
            .astype(str)
            .str.lower()
            == str(entities["relationship"]).lower()
        ]

    # -------------------------
    # TOMORROW'S BIRTHDAYS
    # -------------------------

    if entities.get("relative_date") == "tomorrow":

        tomorrow = today + timedelta(days=1)

        work = work[
            (work.DOB.dt.month == tomorrow.month)
            &
            (work.DOB.dt.day == tomorrow.day)
        ]

    # -------------------------
    # MONTH FILTER
    # -------------------------

    month = entities.get("month")

    if entities.get("relative_month") == "next":

        month = 1 if today.month == 12 else today.month + 1

    if month:

        work = work[
            work.DOB.dt.month == month
        ]

    # -------------------------
    # COUNT BIRTHDAYS
    # -------------------------

    if intent == "count_birthdays":

        return f"I found {len(work)} matching birthdays. 🎉"

    # -------------------------
    # UPCOMING BIRTHDAYS
    # -------------------------

    if intent == "upcoming_birthdays":

        def days_until_birthday(row):

            try:
                candidate = date(
                    today.year,
                    row.DOB.month,
                    row.DOB.day
                )

            except ValueError:
                candidate = date(today.year, 2, 28)

            if candidate < today:

                try:
                    candidate = date(
                        today.year + 1,
                        row.DOB.month,
                        row.DOB.day
                    )

                except ValueError:
                    candidate = date(today.year + 1, 2, 28)

            return (candidate - today).days

        work = work.copy()

        work["_days"] = work.apply(
            days_until_birthday,
            axis=1
        )

        work = work[
            (work["_days"] >= 0)
            &
            (work["_days"] <= 30)
        ]

        work = work.sort_values("_days")

    return format_rows(work)