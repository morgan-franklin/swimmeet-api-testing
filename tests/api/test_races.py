"""
Race Results API Tests
Testing race submissions, results, and rankings
"""

import pytest
import requests

BASE_URL = "http://localhost:5001/api"


class TestRacesEndpoint:
    """Tests for /races endpoint"""

    @pytest.mark.smoke
    def test_get_all_races(self):
        """Test retrieving all race results"""
        # Arrange
        url = f"{BASE_URL}/races"

        # Act
        response = requests.get(url)
        races = response.json()

        # Assert
        assert response.status_code == 200
        assert isinstance(races, list)
        assert len(races) >= 5  # We have 5 initial races
        print(f"\n✓ Retrieved {len(races)} race results")

    def test_submit_race_result(self):
        """Test submitting a new race result"""
        # Arrange
        url = f"{BASE_URL}/races"
        new_race = {
            'swimmer_id': 1,
            'event': '100free',
            'time': '53.45',
            'meet_id': 2,
            'meet_name': 'Winter Championships',
            'lane': 4,
            'heat': 1
        }

        # Act
        response = requests.post(url, json=new_race)
        result = response.json()

        # Assert
        assert response.status_code == 201
        assert result['time'] == new_race['time']
        assert result['event'] == new_race['event']
        assert 'id' in result
        assert 'isPB' in result
        print(f"\n✓ Recorded: {result['event']} - {result['time']} (PB: {result['isPB']})")

    def test_race_result_missing_fields(self):
        """Test that race submission fails without required fields"""
        # Arrange
        url = f"{BASE_URL}/races"
        incomplete_race = {
            'swimmer_id': 1,
            'event': '50free'
            # Missing: time, meet_id
        }

        # Act
        response = requests.post(url, json=incomplete_race)

        # Assert
        assert response.status_code == 400
        assert 'error' in response.json()

    def test_personal_best_detection_first_time(self):
        """Test that first swim in an event is marked as PB"""
        # Arrange
        url = f"{BASE_URL}/races"

        # Use a high swimmer_id that definitely doesn't exist
        first_swim = {
            'swimmer_id': 992,
            'event': '50back',
            'time': '30.50',
            'meet_id': 1
        }

        # Act
        response = requests.post(url, json=first_swim)
        result = response.json()

        # Assert
        assert response.status_code == 201
        assert result['isPB'] == True, f"First swim should be PB, but got isPB={result['isPB']}"

    def test_personal_best_detection_faster_time(self):
        """Test that faster time is marked as PB"""
        # Arrange
        url = f"{BASE_URL}/races"

        # Use unique high swimmer_id
        swimmer_id = 991

        # First, submit a baseline time
        baseline = {
            'swimmer_id': swimmer_id,
            'event': '50free',
            'time': '26.50',
            'meet_id': 1
        }
        baseline_response = requests.post(url, json=baseline)
        assert baseline_response.status_code == 201
        assert baseline_response.json()['isPB'] == True, "First swim should be PB"

        # Then submit a faster time
        faster_time = {
            'swimmer_id': swimmer_id,
            'event': '50free',
            'time': '25.80',  # Faster!
            'meet_id': 2
        }

        # Act
        response = requests.post(url, json=faster_time)
        result = response.json()

        # Assert
        assert response.status_code == 201
        assert result['isPB'] == True, f"Faster time should be PB, got isPB={result['isPB']}"
        print(f"\n✓ New PB detected: {result['time']}")

    def test_filter_races_by_event(self):
        """Test filtering races by event"""
        # Arrange
        event = "50free"
        url = f"{BASE_URL}/races?event={event}"

        # Act
        response = requests.get(url)
        races = response.json()

        # Assert
        assert response.status_code == 200
        for race in races:
            assert race['event'] == event
        print(f"\n✓ Found {len(races)} {event} races")

    def test_filter_races_by_swimmer(self):
        """Test filtering races by swimmer"""
        # Arrange
        swimmer_id = 1
        url = f"{BASE_URL}/races?swimmer_id={swimmer_id}"

        # Act
        response = requests.get(url)
        races = response.json()

        # Assert
        assert response.status_code == 200
        for race in races:
            assert race['swimmer_id'] == swimmer_id
        print(f"\n✓ Swimmer {swimmer_id} has {len(races)} recorded swims")

    def test_get_event_rankings(self):
        """Test retrieving event rankings/leaderboard"""
        # Arrange
        event = "50free"
        url = f"{BASE_URL}/rankings?event={event}"

        # Act
        response = requests.get(url)
        rankings = response.json()

        # Assert
        assert response.status_code == 200
        assert len(rankings) > 0

        # Rankings should have rank numbers
        assert rankings[0]['rank'] == 1

        # Rankings should be sorted by time (fastest first)
        times = [self._time_to_seconds(r['time']) for r in rankings]
        assert times == sorted(times), "Rankings should be sorted fastest to slowest"

        print(f"\n✓ Top 3 in {event}:")
        for ranking in rankings[:3]:
            print(f"   {ranking['rank']}. {ranking['name']} - {ranking['time']} ({ranking['team']})")

    def test_filter_rankings_by_gender(self):
        """Test filtering rankings by gender"""
        # Arrange
        event = "50free"
        gender = "M"
        url = f"{BASE_URL}/rankings?event={event}&gender={gender}"

        # Act
        response = requests.get(url)
        rankings = response.json()

        # Assert
        assert response.status_code == 200

        # Verify all swimmers are male
        for ranking in rankings:
            # Get swimmer details to verify
            swimmer_response = requests.get(f"{BASE_URL}/swimmers/{ranking['swimmer_id']}")
            swimmer = swimmer_response.json()
            assert swimmer['gender'] == gender

    def test_rankings_missing_event(self):
        """Test that rankings requires event parameter"""
        # Arrange
        url = f"{BASE_URL}/rankings"  # No event parameter

        # Act
        response = requests.get(url)

        # Assert
        assert response.status_code == 400
        assert 'error' in response.json()

    def _time_to_seconds(self, time_str):
        """Helper: Convert swim time to seconds for comparison"""
        if ':' in time_str:
            parts = time_str.split(':')
            minutes = int(parts[0])
            seconds = float(parts[1])
            return minutes * 60 + seconds
        return float(time_str)

    @pytest.mark.performance
    def test_rankings_performance(self):
        """Test rankings calculation performance"""
        import time
        url = f"{BASE_URL}/rankings?event=50free"

        start = time.time()
        response = requests.get(url)
        elapsed = time.time() - start

        assert response.status_code == 200
        assert elapsed < 2.0, f"Took {elapsed:.2f}s, should be <2s"
        print(f"\n✓ Rankings: {elapsed:.3f}s")

    @pytest.mark.performance
    def test_race_submission_performance(self):
        """Test race submission performance"""
        import time
        url = f"{BASE_URL}/races"
        race = {
            'swimmer_id': 1,
            'event': '50free',
            'time': '24.99',
            'meet_id': 99
        }

        start = time.time()
        response = requests.post(url, json=race)
        elapsed = time.time() - start

        assert response.status_code == 201
        assert elapsed < 1.0, f"Took {elapsed:.2f}s, should be <1s"
        print(f"\n✓ Submit: {elapsed:.3f}s")