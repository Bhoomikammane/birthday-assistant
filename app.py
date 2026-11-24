from flask import Flask, render_template, request, jsonify, session
import pandas as pd

from nlu import parse
from llm_nlu import parse_with_llm
from service import execute
from dialogue import enrich_with_context, update_state

app = Flask(__name__)

app.secret_key = "birthday-assistant-development-key"

# Load Excel dataset
df = pd.read_excel("data/people.xlsx")

df["DOB"] = pd.to_datetime(df["DOB"], errors="coerce")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():

    message = request.json.get("message", "").strip()

    if not message:
        return jsonify({
            "answer": "Please enter a question! 😊",
            "reply": "Please enter a question! 😊"
        })

    # Get previous conversation state
    state = session.get("dialogue_state", {})

    # =====================================
    # V4: LLM-BASED NLU
    # =====================================

    try:

        parsed = parse_with_llm(message, df)

        nlu_source = "LLM"

    except Exception as error:

        print("LLM failed. Using V3 rule-based NLU.")
        print("Reason:", error)

        # V3 fallback
        parsed = parse(message, df)

        nlu_source = "Rule-based fallback"

    # =====================================
    # V3: DIALOGUE CONTEXT
    # =====================================

    parsed = enrich_with_context(parsed, state)

    entities = parsed["entities"]

    # =====================================
    # AMBIGUITY HANDLING
    # =====================================

    if (
        "relationship" in entities
        and "person_id" not in entities
        and "when is my" in message.lower()
    ):

        matches = df[
            df["Relationship"].fillna("").astype(str).str.lower()
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

            answer = (
                f"I found {len(matches)} people with that relationship: "
                f"{names}. Which person do you mean? 😊"
            )

            return jsonify({
                "answer": answer,
                "reply": answer,
                "debug": parsed,
                "nlu_source": nlu_source
            })

    # =====================================
    # EXECUTE DATABASE QUERY
    # =====================================

    answer = execute(parsed, df)

    # Update conversation memory
    state = update_state(parsed, state)

    session["dialogue_state"] = state

    return jsonify({
        "answer": answer,
        "reply": answer,
        "debug": parsed,
        "state": state,
        "nlu_source": nlu_source
    })


# =====================================
# RESET CONVERSATION
# =====================================

@app.route("/reset", methods=["POST"])
def reset():

    session.clear()

    return jsonify({
        "message": "Conversation reset successfully! 🎂",
        "ok": True
    })


if __name__ == "__main__":

    app.run(debug=True)