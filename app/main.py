import os
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

# ── Database connection from environment variables (no hardcoded secrets) ──
app.config['SQLALCHEMY_DATABASE_URI'] = (
    f"postgresql://{os.environ['DB_USER']}:{os.environ['DB_PASSWORD']}"
    f"@{os.environ['DB_HOST']}:{os.environ.get('DB_PORT', '5432')}/{os.environ['DB_NAME']}"
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ── Model ──────────────────────────────────────────────────────────────────
class Note(db.Model):
    __tablename__ = 'notes'
    id      = db.Column(db.Integer, primary_key=True)
    title   = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created = db.Column(db.DateTime, default=datetime.utcnow)

# ── Routes ─────────────────────────────────────────────────────────────────

# Health check — checks app + real DB connection
@app.route('/health')
def health():
    try:
        db.session.execute(db.text('SELECT 1'))
        return jsonify({'status': 'healthy', 'db': 'connected'}), 200
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'db': str(e)}), 503

# Get all notes
@app.route('/notes', methods=['GET'])
def get_notes():
    notes = Note.query.all()
    return jsonify([{'id': n.id, 'title': n.title,
                      'content': n.content, 'created': n.created.isoformat()}
                     for n in notes])

# Create a note
@app.route('/notes', methods=['POST'])
def create_note():
    data = request.get_json()
    note = Note(title=data['title'], content=data['content'])
    db.session.add(note)
    db.session.commit()
    return jsonify({'id': note.id, 'message': 'Note created'}), 201

# Delete a note
@app.route('/notes/<int:note_id>', methods=['DELETE'])
def delete_note(note_id):
    note = Note.query.get_or_404(note_id)
    db.session.delete(note)
    db.session.commit()
    return jsonify({'message': 'Note deleted'})

# ── Startup ────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    with app.app_context():
        db.create_all()   # creates the 'notes' table if it doesn't exist
    app.run(host='0.0.0.0', port=8000)
