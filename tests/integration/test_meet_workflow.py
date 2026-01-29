"""
Meet Workflow Integration Tests
End-to-end testing of complete swim meet scenarios
"""

import pytest
import requests

BASE_URL = "http://localhost:5001/api"


class TestMeetWorkflow:
    """Integration tests for complete meet workflows"""

    @pytest.mark.integration
    def test_complete_meet_workflow(self):
        """
        Test complete workflow: Register swimmer → Submit race → Check rankings → Verify PB
        This simulates a swimmer competing in their first meet
        """
        # STEP 1: Register new swimmer
        new_swimmer = {
            'name': 'Alex Martinez',
            'age': 26,
            'gender': 'M',
            'team': 'Brooklyn Dolphins',
            'email': 'amartinez@test.com'
        }

        response = requests.post(f"{BASE_URL}/swimmers", json=new_swimmer)
        assert response.status_code == 201
        swimmer_id = response.json()['id']
        print(f"\n✓ Step 1: Registered swimmer ID {swimmer_id}")

        # STEP 2: Submit race result for 50m freestyle
        race_result = {
            'swimmer_id': swimmer_id,
            'event': '50free',
            'time': '25.50',
            'meet_id': 2,
            'meet_name': 'Brooklyn Winter Championship',
            'lane': 4,
            'heat': 1
        }

        response = requests.post(f"{BASE_URL}/races", json=race_result)
        assert response.status_code == 201
        race_data = response.json()
        assert race_data['isPB'] == True, "First swim should always be a PB"
        print(f"✓ Step 2: Submitted race - {race_data['time']} (PB: {race_data['isPB']})")

        # STEP 3: Verify swimmer appears in event rankings
        response = requests.get(f"{BASE_URL}/rankings?event=50free")
        assert response.status_code == 200
        rankings = response.json()

        swimmer_names = [r['name'] for r in rankings]
        assert 'Alex Martinez' in swimmer_names, "Swimmer should appear in rankings"
        print(f"✓ Step 3: Swimmer appears in rankings")

        # STEP 4: Verify personal best was recorded
        response = requests.get(f"{BASE_URL}/swimmers/{swimmer_id}/pbs")
        assert response.status_code == 200
        pbs = response.json()

        assert '50free' in pbs, "PB should be recorded for 50m free"
        assert pbs['50free']['time'] == '25.50'
        assert pbs['50free']['meet'] == 'Brooklyn Winter Championship'
        print(f"✓ Step 4: Personal best recorded: {pbs['50free']['time']}")

        print(f"\n✅ Complete meet workflow validated!")

    @pytest.mark.integration
    def test_multi_event_swimmer(self):
        """
        Test swimmer competing in multiple events in same meet
        """
        # Register swimmer
        swimmer = {
            'name': 'Emma Thompson',
            'age': 24,
            'gender': 'F',
            'team': 'Queens Aquatics'
        }

        response = requests.post(f"{BASE_URL}/swimmers", json=swimmer)
        swimmer_id = response.json()['id']

        # Submit results for 3 different events
        events_and_times = [
            ('50free', '27.80'),
            ('100free', '1:01.50'),
            ('100back', '1:05.20')
        ]

        for event, time in events_and_times:
            race = {
                'swimmer_id': swimmer_id,
                'event': event,
                'time': time,
                'meet_id': 2
            }
            response = requests.post(f"{BASE_URL}/races", json=race)
            assert response.status_code == 201
            assert response.json()['isPB'] == True

        # Verify all PBs recorded
        response = requests.get(f"{BASE_URL}/swimmers/{swimmer_id}/pbs")
        pbs = response.json()

        assert len(pbs) == 3, "Should have 3 personal bests"
        assert '50free' in pbs
        assert '100free' in pbs
        assert '100back' in pbs

        print(f"\n✓ Swimmer competed in {len(events_and_times)} events")
        print(f"✓ All {len(pbs)} personal bests recorded")

    @pytest.mark.integration
    def test_team_competition(self):
        """
        Test multiple swimmers from same team competing
        Simulates team scoring scenario
        """
        team_name = "Manhattan Marlins"

        # Register 3 swimmers from same team
        swimmers = [
            {'name': 'John Smith', 'age': 28, 'gender': 'M', 'team': team_name},
            {'name': 'Jane Doe', 'age': 25, 'gender': 'F', 'team': team_name},
            {'name': 'Bob Wilson', 'age': 30, 'gender': 'M', 'team': team_name}
        ]

        swimmer_ids = []
        for swimmer_data in swimmers:
            response = requests.post(f"{BASE_URL}/swimmers", json=swimmer_data)
            assert response.status_code == 201
            swimmer_ids.append(response.json()['id'])

        # Submit race results for all team members in 50free
        times = ['24.80', '28.50', '25.90']
        for sid, time in zip(swimmer_ids, times):
            race = {
                'swimmer_id': sid,
                'event': '50free',
                'time': time,
                'meet_id': 3
            }
            response = requests.post(f"{BASE_URL}/races", json=race)
            assert response.status_code == 201

        # Check team representation in rankings
        response = requests.get(f"{BASE_URL}/rankings?event=50free")
        rankings = response.json()

        team_swimmers = [r for r in rankings if r['team'] == team_name]
        assert len(team_swimmers) >= 3, f"Should have at least 3 swimmers from {team_name}"

        print(f"\n✓ Registered {len(swimmers)} swimmers from {team_name}")
        print(f"✓ {len(team_swimmers)} team members in 50free rankings")

    @pytest.mark.integration
    def test_age_group_competition(self):
        """
        Test age group filtering in rankings
        Simulates age group award scenario
        """
        # Register swimmers in different age groups
        swimmers = [
            {'name': 'Young Swimmer', 'age': 22, 'gender': 'M', 'team': 'Test Team'},  # 18-24
            {'name': 'Mid Swimmer', 'age': 27, 'gender': 'M', 'team': 'Test Team'},  # 25-29
            {'name': 'Masters Swimmer', 'age': 42, 'gender': 'M', 'team': 'Test Team'}  # 40-44
        ]

        for swimmer_data in swimmers:
            # Register swimmer
            response = requests.post(f"{BASE_URL}/swimmers", json=swimmer_data)
            swimmer_id = response.json()['id']
            age_group = response.json()['ageGroup']

            # Submit race result
            race = {
                'swimmer_id': swimmer_id,
                'event': '100free',
                'time': '58.50',
                'meet_id': 3
            }
            response = requests.post(f"{BASE_URL}/races", json=race)
            assert response.status_code == 201

            print(f"✓ {swimmer_data['name']} (Age {swimmer_data['age']}) → {age_group}")

        # Get rankings for all males
        response = requests.get(f"{BASE_URL}/rankings?event=100free&gender=M")
        all_rankings = response.json()

        assert len(all_rankings) >= 3, "Should have at least 3 male swimmers in rankings"

        # Verify age groups are tracked
        age_groups = set(r['ageGroup'] for r in all_rankings)
        assert '18-24' in age_groups
        assert '25-29' in age_groups
        assert '40-44' in age_groups

        print(f"✓ Found {len(age_groups)} different age groups in rankings")

    @pytest.mark.integration
    def test_personal_best_progression(self):
        """
        Test swimmer improving their time across multiple meets
        Verifies PB detection for progressive improvements
        """
        # Register swimmer
        swimmer = {
            'name': 'Progressive Swimmer',
            'age': 29,
            'gender': 'F',
            'team': 'Bronx Barracudas'
        }

        response = requests.post(f"{BASE_URL}/swimmers", json=swimmer)
        swimmer_id = response.json()['id']

        # Simulate 4 meets with varying times
        meets_and_times = [
            (1, '30.50'),  # First meet - will be PB
            (2, '29.80'),  # Improved - will be PB
            (3, '30.10'),  # Slower - NOT a PB
            (4, '29.50')  # Best time - will be PB
        ]

        pb_count = 0
        for meet_id, time in meets_and_times:
            race = {
                'swimmer_id': swimmer_id,
                'event': '50free',
                'time': time,
                'meet_id': meet_id
            }

            response = requests.post(f"{BASE_URL}/races", json=race)
            is_pb = response.json()['isPB']

            if is_pb:
                pb_count += 1
                print(f"✓ Meet {meet_id}: {time} - NEW PB! 🎉")
            else:
                print(f"  Meet {meet_id}: {time} - Not a PB")

        # Verify final PB is the fastest time
        response = requests.get(f"{BASE_URL}/swimmers/{swimmer_id}/pbs")
        pbs = response.json()

        assert pbs['50free']['time'] == '29.50', "Final PB should be fastest time"
        assert pb_count == 3, "Should have 3 PBs total (meets 1, 2, and 4)"

        print(f"\n✓ Swimmer achieved {pb_count} personal bests across 4 meets")
        print(f"✓ Final PB: {pbs['50free']['time']}")