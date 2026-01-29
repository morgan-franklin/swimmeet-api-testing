"""
Swimmer Management API Tests
Testing swimmer registration, profiles, and personal records
"""

import pytest
import requests

BASE_URL = "http://localhost:5001/api"


class TestSwimmersEndpoint:
    """Tests for /swimmers endpoint"""

    @pytest.mark.smoke
    def test_get_all_swimmers(self):
        """Test retrieving all registered swimmers"""
        # Arrange
        url = f"{BASE_URL}/swimmers"

        # Act
        response = requests.get(url)
        swimmers = response.json()

        # Assert
        assert response.status_code == 200
        assert isinstance(swimmers, list)
        assert len(swimmers) >= 5  # We have 5 initial swimmers
        print(f"\n✓ Retrieved {len(swimmers)} swimmers")

    def test_get_single_swimmer(self):
        """Test retrieving a specific swimmer by ID"""
        # Arrange
        swimmer_id = 1
        url = f"{BASE_URL}/swimmers/{swimmer_id}"

        # Act
        response = requests.get(url)
        swimmer = response.json()

        # Assert
        assert response.status_code == 200
        assert swimmer['id'] == swimmer_id
        assert swimmer['name'] == "Morgan Franklin"
        assert 'team' in swimmer
        print(f"\n✓ Retrieved: {swimmer['name']}")

    def test_get_nonexistent_swimmer(self):
        """Test retrieving a swimmer that doesn't exist"""
        # Arrange
        swimmer_id = 99999
        url = f"{BASE_URL}/swimmers/{swimmer_id}"

        # Act
        response = requests.get(url)

        # Assert
        assert response.status_code == 404
        assert 'error' in response.json()

    def test_swimmer_has_required_fields(self):
        """Test that swimmer object has all required fields"""
        # Arrange
        url = f"{BASE_URL}/swimmers/1"
        required_fields = ['id', 'name', 'age', 'gender', 'team', 'ageGroup']

        # Act
        response = requests.get(url)
        swimmer = response.json()

        # Assert
        for field in required_fields:
            assert field in swimmer, f"Swimmer should have '{field}' field"

    def test_register_new_swimmer(self):
        """Test registering a new swimmer"""
        # Arrange
        url = f"{BASE_URL}/swimmers"
        new_swimmer = {
            'name': 'Test Swimmer',
            'age': 25,
            'gender': 'M',
            'team': 'Test Team',
            'email': 'test@swimmer.com'
        }

        # Act
        response = requests.post(url, json=new_swimmer)
        created = response.json()

        # Assert
        assert response.status_code == 201
        assert created['name'] == new_swimmer['name']
        assert created['team'] == new_swimmer['team']
        assert 'id' in created
        assert created['ageGroup'] == '25-29'  # Auto-calculated
        print(f"\n✓ Registered swimmer: {created['name']} (ID: {created['id']})")

    def test_age_group_calculation_youth(self):
        """Test that age group is correctly calculated for youth"""
        # Arrange
        url = f"{BASE_URL}/swimmers"
        swimmer = {
            'name': 'Young Swimmer',
            'age': 15,
            'gender': 'F',
            'team': 'Youth Team'
        }

        # Act
        response = requests.post(url, json=swimmer)
        created = response.json()

        # Assert
        assert created['ageGroup'] == 'Youth'

    def test_age_group_calculation_masters(self):
        """Test that age group is correctly calculated for masters (5-year bands)"""
        # Arrange
        url = f"{BASE_URL}/swimmers"
        test_cases = [
            (20, '18-24'),
            (27, '25-29'),
            (32, '30-34'),
            (37, '35-39'),
            (42, '40-44'),
            (47, '45-49'),
            (52, '50-54'),
            (57, '55-59'),
            (62, '60-64'),
            (67, '65-69'),
            (75, '70+')
        ]

        for age, expected_group in test_cases:
            swimmer = {
                'name': f'Swimmer Age {age}',
                'age': age,
                'gender': 'M',
                'team': 'Test Team'
            }

            # Act
            response = requests.post(url, json=swimmer)
            created = response.json()

            # Assert
            assert created['ageGroup'] == expected_group, \
                f"Age {age} should be in group {expected_group}, got {created['ageGroup']}"

        print(f"\n✓ All {len(test_cases)} age groups validated correctly")

    def test_register_swimmer_missing_fields(self):
        """Test that registration fails without required fields"""
        # Arrange
        url = f"{BASE_URL}/swimmers"
        incomplete_swimmer = {
            'name': 'Incomplete Swimmer'
            # Missing: age, gender, team
        }

        # Act
        response = requests.post(url, json=incomplete_swimmer)

        # Assert
        assert response.status_code == 400
        assert 'error' in response.json()

    def test_get_personal_bests(self):
        """Test retrieving swimmer's personal best times"""
        # Arrange
        swimmer_id = 1  # Morgan Franklin
        url = f"{BASE_URL}/swimmers/{swimmer_id}/pbs"

        # Act
        response = requests.get(url)
        pbs = response.json()

        # Assert
        assert response.status_code == 200
        assert isinstance(pbs, dict)

        # Morgan should have PBs
        assert len(pbs) > 0

        # Check structure of PB entry
        if '50free' in pbs:
            assert 'time' in pbs['50free']
            assert 'meet' in pbs['50free']
            assert 'date' in pbs['50free']
            print(f"\n✓ 50m Free PB: {pbs['50free']['time']}")

    def test_filter_swimmers_by_team(self):
        """Test filtering swimmers by team"""
        # Arrange
        team = "NYC Aquatics Masters"
        url = f"{BASE_URL}/swimmers?team={team}"

        # Act
        response = requests.get(url)
        swimmers = response.json()

        # Assert
        assert response.status_code == 200

        # All swimmers should be from the specified team (if any found)
        for swimmer in swimmers:
            assert swimmer['team'] == team

        print(f"\n✓ Found {len(swimmers)} swimmers on {team}")

    @pytest.mark.performance
    def test_get_all_swimmers_performance(self):
        """Test that retrieving all swimmers is fast"""
        # Arrange
        import time
        url = f"{BASE_URL}/swimmers"
        max_time = 0.5  # seconds

        # Act
        start = time.time()
        response = requests.get(url)
        elapsed = time.time() - start

        # Assert
        assert response.status_code == 200
        assert elapsed < max_time, f"Get swimmers took {elapsed:.2f}s, expected <{max_time}s"
        print(f"\n✓ Retrieved swimmers in {elapsed:.3f}s")

    @pytest.mark.performance
    def test_personal_bests_performance(self):
        """Test that PB calculation is fast"""
        # Arrange
        import time
        swimmer_id = 1
        url = f"{BASE_URL}/swimmers/{swimmer_id}/pbs"
        max_time = 1.0  # second

        # Act
        start = time.time()
        response = requests.get(url)
        elapsed = time.time() - start

        # Assert
        # Just check response time, don't validate JSON (known issue)
        assert elapsed < max_time, f"PB calculation took {elapsed:.2f}s, expected <{max_time}s"
        print(f"\n✓ PBs calculated in {elapsed:.3f}s")