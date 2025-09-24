from flask import Flask, render_template, request, jsonify
import sqlite3
import random
from sentence_transformers import SentenceTransformer, util
from difflib import SequenceMatcher

DB_PATH = r"story_game_full.db"
SIMILARITY_THRESHOLD = 0.7
FUZZY_THRESHOLD = 0.7

app = Flask(__name__)
model = SentenceTransformer("all-mpnet-base-v2")
fallback_log = {}
current_stage = 1

# ----------------------------
# Utility functions
# ----------------------------
def fetch_stage(stage):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM story WHERE stage=?", (stage,))
    row = c.fetchone()
    conn.close()
    return row

def fuzzy_match_keyword(word, user_input):
    user_words = user_input.lower().split()
    for uw in user_words:
        if SequenceMatcher(None, word.lower(), uw).ratio() >= FUZZY_THRESHOLD:
            return True
    return False

def check_keywords(keywords, user_input):
    return all(fuzzy_match_keyword(k, user_input) for k in keywords.split(","))

# ----------------------------
# Routes
# ----------------------------
@app.route("/")
def index():
    stage = fetch_stage(current_stage)
    clue = stage[4] if stage else "No clue available."
    return render_template("index.html", clue=clue)

@app.route("/play", methods=["POST"])
def play():
    global current_stage, fallback_log

    user_input = request.json.get("input", "").strip()
    if user_input.lower() in ["exit", "quit"]:
        return jsonify({"message": "Exiting game.", "completed": True})

    row = fetch_stage(current_stage)
    if not row:
        return jsonify({"message": "🎉 Congratulations! You completed the story! 🎉", "completed": True})

    stage_num, character, ideal_prompt, keywords, clue, *fallbacks = row

    sim = util.cos_sim(
        model.encode(user_input, convert_to_tensor=True),
        model.encode(ideal_prompt, convert_to_tensor=True)
    ).item()

    kws_ok = check_keywords(keywords, user_input)

    if kws_ok and sim >= SIMILARITY_THRESHOLD:
        current_stage += 1
        fallback_log[current_stage] = []
        next_stage = fetch_stage(current_stage)
        next_clue = next_stage[4] if next_stage else ""
        progress = int((current_stage-1)/12*100)
        return jsonify({
            "message": f"✅ {character} nods, eyes glinting with understanding. You may proceed.",
            "completed": False,
            "progress": progress,
            "clue": next_clue,
            "passed": True
        })
    else:
        used = fallback_log.get(current_stage, [])
        available_fallbacks = [fb for fb in fallbacks if fb not in used]
        if not available_fallbacks:
            available_fallbacks = fallbacks
        fb_choice = random.choice(available_fallbacks)
        used.append(fb_choice)
        fallback_log[current_stage] = used
        progress = int((current_stage-1)/12*100)
        return jsonify({
            "message": fb_choice,
            "completed": False,
            "progress": progress,
            "clue": clue,
            "passed": False
        })

if __name__ == "__main__":
    app.run(debug=True)
