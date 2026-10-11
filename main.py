# smart_event_manager.py
from flask import Flask, jsonify, request, send_from_directory
from flask import Response
from flask_sqlalchemy import SQLAlchemy
from threading import Thread
import random

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///events.db'
db = SQLAlchemy(app)

# ---------- Models ----------
user_event = db.Table('user_event',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('event_id', db.Integer, db.ForeignKey('event.id'))
)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    events = db.relationship('Event', secondary=user_event, backref='attendees')

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    category = db.Column(db.String(50))

    def to_dict(self):
        return {"id": self.id, "title": self.title, "category": self.category}

# ---------- ML Recommender ----------
def recommend_events(user_id, events):
    # Simple random recommender
    return random.sample(events, min(3, len(events)))

# ---------- Flask Routes ----------
@app.route('/events', methods=['GET'])
def get_events():
    events = Event.query.all()
    return jsonify([e.to_dict() for e in events])

@app.route('/register', methods=['POST'])
def register_event():
    data = request.json
    user = User.query.get(data['user_id'])
    event = Event.query.get(data['event_id'])
    if user and event:
        user.events.append(event)
        db.session.commit()
        return jsonify({'status': 'success'})
    return jsonify({'status': 'failure'}), 400

@app.route('/recommend/<int:user_id>', methods=['GET'])
def recommend(user_id):
    events = Event.query.all()
    event_dicts = [e.to_dict() for e in events]
    recommendations = recommend_events(user_id, event_dicts)
    return jsonify(recommendations)

# ---------- Serve Frontend ----------
FRONTEND_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Smart Event Manager</title>
  <style>
    body { font-family: Arial; margin: 20px; }
    h1,h2 { color:#2c3e50; }
    ul { list-style:none; padding-left:0; }
    li { background:#ecf0f1; margin:5px 0; padding:10px; border-radius:5px; }
  </style>
</head>
<body>
<h1>Smart Event Manager</h1>

<section id="events">
  <h2>Available Events</h2>
  <ul id="event-list"></ul>
</section>

<section id="recommendations">
  <h2>Recommended Events</h2>
  <ul id="recommendation-list"></ul>
</section>

<script>
fetch("/events")
  .then(res => res.json())
  .then(events => {
    const list = document.getElementById("event-list");
    events.forEach(e => { let li = document.createElement("li"); li.textContent = e.title + " - " + e.category; list.appendChild(li); });
  });

fetch("/recommend/1")
  .then(res => res.json())
  .then(recs => {
    const list = document.getElementById("recommendation-list");
    recs.forEach(e => { let li = document.createElement("li"); li.textContent = e.title; list.appendChild(li); });
  });
</script>
</body>
</html>
"""

@app.route('/')
def index():
    return Response(FRONTEND_HTML, mimetype='text/html')

# ---------- Agent Simulation ----------
def agent_task():
    # Example: print recommendations periodically
    events = Event.query.all()
    event_dicts = [e.to_dict() for e in events]
    recs = recommend_events(1, event_dicts)
    print("Agent Recommended Events:", [r['title'] for r in recs])

def run_agent():
    import time
    while True:
        agent_task()
        time.sleep(15)

# ---------- Main ----------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        if not Event.query.first():
            db.session.add_all([
                Event(title="Music Festival", category="Music"),
                Event(title="Tech Meetup", category="Tech"),
                Event(title="Art Expo", category="Art"),
                Event(title="Startup Pitch", category="Business"),
            ])
            db.session.add(User(id=1, name="Alice"))
            db.session.commit()

    # Start agent in a separate thread
    Thread(target=run_agent, daemon=True).start()

    # Start Flask server
    app.run(host='0.0.0.0', port=5000, debug=True)
