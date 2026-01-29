"""
Events API Endpoint Tests
Testing swim event definitions and reference data
"""

import pytest
import requests

BASE_URL = "http://localhost:5001/api"


class TestEventsEndpoint:
    """Tests for /events endpoint"""

    @pytest.mark.smoke
    def test_get_all_events(self):
        """Test retrieving all swim events"""
        # Arrange
        url = f"{BASE_URL}/events"

        # Act
        response = requests.get(url)
        events = response.json()

        # Assert
        assert response.status_code == 200
        assert isinstance(events, list)
        assert len(events) >= 9  # We have 9 events defined
        print(f"\n✓ Retrieved {len(events)} events")

    def test_events_have_required_fields(self):
        """Test that all events have required fields"""
        # Arrange
        url = f"{BASE_URL}/events"
        required_fields = ['id', 'name', 'code', 'distance', 'stroke', 'pool']

        # Act
        response = requests.get(url)
        events = response.json()

        # Assert
        assert len(events) > 0
        for event in events:
            for field in required_fields:
                assert field in event, f"Event {event.get('name', '?')} should have '{field}' field"

        print(f"\n✓ All {len(events)} events have required fields")

    def test_event_codes_format(self):
        """Test that event codes follow expected format"""
        # Arrange
        url = f"{BASE_URL}/events"

        # Act
        response = requests.get(url)
        events = response.json()

        # Assert
        for event in events:
            code = event['code']
            # Event codes should not contain spaces
            assert ' ' not in code, f"Code '{code}' should not contain spaces"

        print(f"\n✓ All event codes properly formatted")

    @pytest.mark.parametrize("expected_event", [
        "50free",
        "100free",
        "200free",
        "1500free",
        "100back",
        "100breast",
        "100fly",
        "200IM",
        "400IM"
    ])
    def test_all_events_exist(self, expected_event):
        """Test that all 9 standard events exist"""
        # Arrange
        url = f"{BASE_URL}/events"

        # Act
        response = requests.get(url)
        events = response.json()
        event_codes = [e['code'] for e in events]

        # Assert
        assert expected_event in event_codes, \
            f"Expected event '{expected_event}' should exist"

    def test_events_have_valid_distances(self):
        """Test that event distances are realistic"""
        # Arrange
        url = f"{BASE_URL}/events"
        valid_distances = [50, 100, 200, 400, 800, 1500]

        # Act
        response = requests.get(url)
        events = response.json()

        # Assert
        for event in events:
            distance = event['distance']
            assert distance in valid_distances, \
                f"Distance {distance}m for {event['name']} is not a standard swim distance"

        print(f"\n✓ All distances are valid")

    def test_events_have_valid_strokes(self):
        """Test that event strokes are valid"""
        # Arrange
        url = f"{BASE_URL}/events"
        valid_strokes = ['freestyle', 'backstroke', 'breaststroke', 'butterfly', 'im']

        # Act
        response = requests.get(url)
        events = response.json()

        # Assert
        for event in events:
            stroke = event['stroke']
            assert stroke in valid_strokes, \
                f"Stroke '{stroke}' for {event['name']} is not a valid stroke type"

        print(f"\n✓ All strokes are valid")

    def test_freestyle_events_count(self):
        """Test that we have all freestyle events"""
        # Arrange
        url = f"{BASE_URL}/events"

        # Act
        response = requests.get(url)
        events = response.json()

        # Assert
        freestyle_events = [e for e in events if e['stroke'] == 'freestyle']
        assert len(freestyle_events) == 4, "Should have 4 freestyle events (50, 100, 200, 1500)"

        distances = [e['distance'] for e in freestyle_events]
        assert 50 in distances
        assert 100 in distances
        assert 200 in distances
        assert 1500 in distances

        print(f"\n✓ All 4 freestyle distances present")

    def test_im_events_count(self):
        """Test that we have both IM events"""
        # Arrange
        url = f"{BASE_URL}/events"

        # Act
        response = requests.get(url)
        events = response.json()

        # Assert
        im_events = [e for e in events if e['stroke'] == 'im']
        assert len(im_events) == 2, "Should have 2 IM events (200, 400)"

        distances = [e['distance'] for e in im_events]
        assert 200 in distances
        assert 400 in distances

        print(f"\n✓ Both IM events present (200IM, 400IM)")