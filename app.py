from flask import Flask, render_template, request, jsonify, session
import pandas as pd

from nlu import parse
from service import execute
from dialogue import enrich_with_context, update_state


app = Flask(__name__)

# Development secret key for Flask sessions
app.secret_key = "birthday-assistant-development-key"


# Load Excel dataset
df = pd.read_excel("data/people.xlsx")

df["DOB"] = pd.to_datetime(df["DOB"], errors="coerce")


# Home page
@app.route("/")
def index():

    return render_template("index.html")


# Chat endpoint
@app.route("/chat", methods=["POST"])
def chat():

    message = request.json.get("message", "")

    # Get previous conversation state
    state = session.get("dialogue_state", {})

    # Parse current message
    parsed = parse(message, df)

    # Add previous context if required
    parsed = enrich_with_context(parsed, state)

    entities = parsed["entities"]

    # --------------------------------
    # AMBIGUITY DETECTION
    # --------------------------------

    if (
        "relationship" in entities
        and "person_id" not in entities
        and "when is my" in message.lower()
    ):

        matches = df[
            df["Relationship"]
            .fillna("")
            .astype(str)
            .str.lower()
            == str(entities["relationship"]).lower()
        ]

        if len(matches) > 1:

            names = ", ".join(
                matches["Name"].head(8).tolist()
            )

            state = update_state(
                parsed,
                state,
                matches["Person_ID"].tolist()
            )

            session["dialogue_state"] = state

            return jsonify({
                "answer": (
                    f"I found {len(matches)} people "
                    f"with that relationship: {names}. "
                    "Which person do you mean? 😊"
                ),
                "reply": (
                    f"I found {len(matches)} people "
                    f"with that relationship: {names}. "
                    "Which person do you mean? 😊"
                ),
                "debug": parsed
            })

    # --------------------------------
    # EXECUTE QUERY
    # --------------------------------

    answer = execute(parsed, df)

    # Update conversation state
    state = update_state(parsed, state)

    session["dialogue_state"] = state

    return jsonify({
        "answer": answer,
        "reply": answer,
        "debug": parsed,
        "state": state
    })


# RESET CONVERSATION
@app.route("/reset", methods=["POST"])
def reset():

    session.clear()

    return jsonify({
        "message": "Conversation reset successfully! 🎂",
        "ok": True
    })


if __name__ == "__main__":

    app.run(debug=True)