"""
SwimMeet Mock API
A simple Flask API for swim meet management testing
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import json
from pathlib import Path
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Load data files
DATA_DIR = Path(__file__).parent / 'data'


def load_data(filename):
    with open(DATA_DIR / filename, 'r') as f:
        return json.load(f)


def save_data(filename, data):
    with open(DATA_DIR / filename, 'w') as f:
        json.dump(data, f, indent=2)


# Initialize data
swimmers = load_data('swimmers.json')
events = load_data('events.json')
races = load_data('race_results.json')


# ============================================================================
# SWIMMERS ENDPOINTS
# ============================================================================

@app.route('/api/swimmers', methods=['GET', 'POST'])
def handle_swimmers():

    if request.method == 'GET':
        team = request.args.get('team')
        if team:
            return jsonify([s for s in swimmers if s['team'].lower() == team.lower()])
        return jsonify(swimmers)

    elif request.method == 'POST':
        if not request.is_json:
            return jsonify({'error': 'Request body must be JSON'}), 400

        new_swimmer = request.json
        required = ['name', 'age', 'gender', 'team']
        if not all(field in new_swimmer for field in required):
            return jsonify({'error': 'Missing required fields'}), 400

        new_swimmer['id'] = max([s['id'] for s in swimmers]) + 1 if swimmers else 1

        age = new_swimmer['age']
        if age < 18:
            new_swimmer['ageGroup'] = 'Youth'
        elif age <= 24:
            new_swimmer['ageGroup'] = '18-24'
        elif age <= 29:
            new_swimmer['ageGroup'] = '25-29'
        elif age <= 34:
            new_swimmer['ageGroup'] = '30-34'
        elif age <= 39:
            new_swimmer['ageGroup'] = '35-39'
        elif age <= 44:
            new_swimmer['ageGroup'] = '40-44'
        elif age <= 49:
            new_swimmer['ageGroup'] = '45-49'
        elif age <= 54:
            new_swimmer['ageGroup'] = '50-54'
        elif age <= 59:
            new_swimmer['ageGroup'] = '55-59'
        elif age <= 64:
            new_swimmer['ageGroup'] = '60-64'
        elif age <= 69:
            new_swimmer['ageGroup'] = '65-69'
        else:
            new_swimmer['ageGroup'] = '70+'

        swimmers.append(new_swimmer)
        save_data('swimmers.json', swimmers)
        return jsonify(new_swimmer), 201


@app.route('/api/swimmers/<int:swimmer_id>', methods=['GET', 'PUT', 'DELETE'])
def handle_swimmer(swimmer_id):

    swimmer = next((s for s in swimmers if s['id'] == swimmer_id), None)

    if request.method == 'GET':
        if swimmer:
            return jsonify(swimmer)
        return jsonify({'error': 'Swimmer not found'}), 404

    elif request.method == 'PUT':
        if not swimmer:
            return jsonify({'error': 'Swimmer not found'}), 404
        swimmer.update(request.json or {})
        save_data('swimmers.json', swimmers)
        return jsonify(swimmer)

    elif request.method == 'DELETE':
        if not swimmer:
            return jsonify({'error': 'Swimmer not found'}), 404
        swimmers.remove(swimmer)
        save_data('swimmers.json', swimmers)
        return jsonify({'message': 'Swimmer deleted'}), 200


# ============================================================================
# RACES ENDPOINTS
# ============================================================================

@app.route('/api/races', methods=['GET', 'POST'])
def handle_races():

    if request.method == 'GET':
        event = request.args.get('event')
        meet_id = request.args.get('meet_id')
        swimmer_id = request.args.get('swimmer_id')

        filtered = races
        if event:
            filtered = [r for r in filtered if r['event'] == event]
        if meet_id:
            filtered = [r for r in filtered if r['meet_id'] == int(meet_id)]
        if swimmer_id:
            filtered = [r for r in filtered if r['swimmer_id'] == int(swimmer_id)]

        return jsonify(filtered), 200

    elif request.method == 'POST':
        if not request.is_json:
            return jsonify({'error': 'Request body must be JSON'}), 400

        new_race = request.json
        required = ['swimmer_id', 'event', 'time', 'meet_id']
        if not all(field in new_race for field in required):
            return jsonify({'error': 'Missing required fields'}), 400

        new_race['id'] = max([r['id'] for r in races]) + 1 if races else 1

        swimmer_id = new_race['swimmer_id']
        event = new_race['event']
        new_time_seconds = time_to_seconds(new_race['time'])

        existing_times = [
            time_to_seconds(r['time'])
            for r in races
            if r['swimmer_id'] == swimmer_id and r['event'] == event
        ]

        new_race['isPB'] = (
            len(existing_times) == 0 or
            new_time_seconds < min(existing_times)
        )

        if 'date' not in new_race:
            new_race['date'] = datetime.now().strftime('%Y-%m-%d')

        races.append(new_race)
        save_data('race_results.json', races)
        return jsonify(new_race), 201


# ============================================================================
# RANKINGS ENDPOINT
# ============================================================================

@app.route('/api/rankings', methods=['GET'])
def get_rankings():
    """Get rankings/leaderboard for an event"""

    event = request.args.get('event')
    gender = request.args.get('gender')
    age_group = request.args.get('ageGroup')

    if not event:
        return jsonify({'error': 'Event parameter required'}), 400

    # Filter races by event
    event_races = [r for r in races if r['event'] == event]

    # Get best time per swimmer
    best_times = {}
    for race in event_races:
        sid = race['swimmer_id']
        time_seconds = time_to_seconds(race['time'])

        if sid not in best_times or time_seconds < best_times[sid]['seconds']:
            best_times[sid] = {
                'time': race['time'],
                'seconds': time_seconds,
                'meet': race.get('meet_name', 'Unknown'),
                'date': race.get('date', 'Unknown')
            }

    # Build rankings
    rankings = []
    for sid, time_data in best_times.items():
        swimmer = next((s for s in swimmers if s['id'] == sid), None)
        if not swimmer:
            continue

        # Apply filters
        if gender and swimmer['gender'] != gender:
            continue
        if age_group and swimmer.get('ageGroup') != age_group:
            continue

        rankings.append({
            'rank': 0,  # Will be set after sorting
            'swimmer_id': sid,
            'name': swimmer['name'],
            'team': swimmer['team'],
            'age': swimmer['age'],
            'ageGroup': swimmer.get('ageGroup', 'Unknown'),  # ⭐ ADD THIS
            'time': time_data['time'],
            'meet': time_data['meet'],
            'date': time_data['date']
        })

    # Sort by time and assign ranks
    rankings.sort(key=lambda x: time_to_seconds(x['time']))
    for i, ranking in enumerate(rankings):
        ranking['rank'] = i + 1

    return jsonify(rankings)


# ============================================================================
# PBS ENDPOINT
# ============================================================================

@app.route('/api/swimmers/<int:swimmer_id>/pbs', methods=['GET'])
def get_personal_bests(swimmer_id):
    """Get swimmer's personal best times"""

    swimmer_races = [r for r in races if r['swimmer_id'] == swimmer_id]

    if not swimmer_races:
        return jsonify({})

    # Calculate PBs per event
    pbs = {}
    for race in swimmer_races:
        event = race['event']
        time = race['time']

        # Convert time to seconds for comparison
        time_seconds = time_to_seconds(time)

        if event not in pbs:
            pbs[event] = {
                'time': time,
                'meet': race.get('meet_name', 'Unknown'),
                'date': race.get('date', 'Unknown')
            }
        else:
            pb_seconds = time_to_seconds(pbs[event]['time'])
            if time_seconds < pb_seconds:
                pbs[event] = {
                    'time': time,
                    'meet': race.get('meet_name', 'Unknown'),
                    'date': race.get('date', 'Unknown')
                }

    return jsonify(pbs)


# ============================================================================
# EVENTS
# ============================================================================

@app.route('/api/events', methods=['GET'])
def get_events():
    return jsonify(events), 200


# ============================================================================
# UTIL
# ============================================================================

def time_to_seconds(time_str):
    if ':' in time_str:
        m, s = time_str.split(':')
        return int(m) * 60 + float(s)
    return float(time_str)


# ============================================================================
# HEALTH
# ============================================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'swimmers_count': len(swimmers),
        'races_count': len(races),
        'events_count': len(events)
    }), 200


# ============================================================================
# RUN SERVER
# ============================================================================

if __name__ == '__main__':
    print("🏊 SwimMeet API starting...")
    print("📍 Running on http://localhost:5000")
    print("📚 API endpoints:")
    print("   GET  /api/swimmers")
    print("   POST /api/swimmers")
    print("   GET  /api/races")
    print("   POST /api/races")
    print("   GET  /api/rankings?event=50free")
    print("   GET  /api/health")
    app.run(debug=True, port=5001)