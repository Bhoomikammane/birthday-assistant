from flask import Flask, render_template, request, jsonify
import pandas as pd

from nlu import parse
from service import execute

app = Flask(__name__)

# Load Excel dataset
df = pd.read_excel("data/people.xlsx")

df["DOB"] = pd.to_datetime(df["DOB"], errors="coerce")

# Home page
@app.route("/")
def index():
    return render_template("index.html")


# Chat API
@app.route("/chat", methods=["POST"])
def chat():

    message = request.json.get("message", "")

    # Identify intent and entities
    parsed = parse(message, df)

    # Execute the query
    answer = execute(parsed, df)

    return jsonify({
        "answer": answer,
        "reply": answer,
        "debug": parsed
    })


if __name__ == "__main__":
    app.run(debug=True)