import json
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_swagger_ui import get_swaggerui_blueprint
import requests

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///events.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Instructions for flask-swagger-ui
SWAGGER_URL = "/api/docs"
API_URL = "/static/PoliceEvents-API.yaml"

swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "Police Events API"
    }
)

app.register_blueprint(swaggerui_blueprint)

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    external_id = db.Column(db.String(50), unique=True, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    summary = db.Column(db.Text, nullable=False)
    url = db.Column(db.String(500), nullable=False)
    type = db.Column(db.String(100), nullable=True)
    location = db.Column(db.String(200), nullable=True)
    datetime = db.Column(db.String(50), nullable=True)

    def __repr__(self):
        return f"Event('{self.title}')"

# This line ensures that we create the tables in the proper application context
with app.app_context():
    db.create_all()

@app.route('/api/v1/events', methods=['GET'])
def get_events():
    events = Event.query.all()
    if not events:  # If there are no events in the database, fetch them from the police API
        response = requests.get('https://polisen.se/api/events')
        events_data = response.json()
        # Add events to the database
        for event_data in events_data:
            event = Event(
                external_id=event_data['id'],
                title=event_data['name'],
                summary=event_data['summary'],
                url=event_data['url'],
                type=event_data['type'],
                location=event_data['location']['name'],
                datetime=event_data['datetime']
            )
            db.session.add(event)
        db.session.commit()
        events = Event.query.all()

    events_list = [{
        "id": event.external_id,
        "title": event.title,
        "summary": event.summary,
        "url": event.url,
        "type": event.type,
        "location": event.location,
        "datetime": event.datetime
    } for event in events]

    return jsonify(events_list), 200


@app.route('/api/v1/events', methods=['POST'])
def create_event():
    data = json.loads(request.data)
    event = Event(
        external_id=data['id'],
        title=data['title'],
        summary=data['summary'],
        url=data['url'],
        type=data['type'],
        location=data['location'],
        datetime=data['datetime']
    )

    db.session.add(event)
    db.session.commit()

    response = jsonify(event.external_id), 201
    response[0].headers.set('Location', f'/api/v1/events/{event.external_id}')
    return response

if __name__ == '__main__':
    app.run(debug=True)
