"""
Tests for FastAPI activities endpoints using AAA (Arrange-Act-Assert) pattern.
"""

import pytest
from src.app import activities


class TestGetActivities:
    """Test cases for GET /activities endpoint."""

    def test_get_all_activities_success(self, client):
        """Test successful retrieval of all activities."""
        # Arrange - No special setup needed, using default activities

        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) == 9  # All 9 activities should be returned
        assert "Chess Club" in data
        assert "Programming Class" in data

        # Verify structure of returned data
        chess_club = data["Chess Club"]
        assert "description" in chess_club
        assert "schedule" in chess_club
        assert "max_participants" in chess_club
        assert "participants" in chess_club
        assert isinstance(chess_club["participants"], list)


class TestSignupForActivity:
    """Test cases for POST /activities/{activity_name}/signup endpoint."""

    def test_signup_success(self, client, reset_activities):
        """Test successful signup for an activity."""
        # Arrange
        activity_name = "Chess Club"
        new_email = "test@mergington.edu"

        # Verify email is not already signed up
        initial_participants = activities[activity_name]["participants"].copy()
        assert new_email not in initial_participants

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": new_email}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert f"Signed up {new_email} for {activity_name}" == data["message"]

        # Verify participant was added
        assert new_email in activities[activity_name]["participants"]
        assert len(activities[activity_name]["participants"]) == len(initial_participants) + 1

    def test_signup_activity_not_found(self, client):
        """Test signup with non-existent activity."""
        # Arrange
        invalid_activity = "NonExistent Activity"
        email = "test@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{invalid_activity}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Activity not found"

    def test_signup_already_registered(self, client, reset_activities):
        """Test signup when student is already registered."""
        # Arrange
        activity_name = "Chess Club"
        existing_email = "michael@mergington.edu"  # Already in Chess Club

        # Verify email is already signed up
        assert existing_email in activities[activity_name]["participants"]

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": existing_email}
        )

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert data["detail"] == "Student already signed up for this activity"

        # Verify no duplicate was added
        assert activities[activity_name]["participants"].count(existing_email) == 1


class TestRemoveParticipant:
    """Test cases for DELETE /activities/{activity_name}/participant endpoint."""

    def test_remove_participant_success(self, client, reset_activities):
        """Test successful removal of a participant."""
        # Arrange
        activity_name = "Chess Club"
        email_to_remove = "michael@mergington.edu"

        # Verify participant exists
        initial_participants = activities[activity_name]["participants"].copy()
        assert email_to_remove in initial_participants

        # Act
        response = client.delete(
            f"/activities/{activity_name}/participant",
            params={"email": email_to_remove}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert f"Removed {email_to_remove} from {activity_name}" == data["message"]

        # Verify participant was removed
        assert email_to_remove not in activities[activity_name]["participants"]
        assert len(activities[activity_name]["participants"]) == len(initial_participants) - 1

    def test_remove_participant_activity_not_found(self, client):
        """Test removal with non-existent activity."""
        # Arrange
        invalid_activity = "NonExistent Activity"
        email = "test@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{invalid_activity}/participant",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Activity not found"

    def test_remove_participant_not_registered(self, client, reset_activities):
        """Test removal when participant is not registered."""
        # Arrange
        activity_name = "Chess Club"
        non_participant_email = "notregistered@mergington.edu"

        # Verify email is not registered
        assert non_participant_email not in activities[activity_name]["participants"]

        # Act
        response = client.delete(
            f"/activities/{activity_name}/participant",
            params={"email": non_participant_email}
        )

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert data["detail"] == "Participant not found in this activity"


class TestRootEndpoint:
    """Test cases for GET / root endpoint."""

    def test_root_redirect(self, client):
        """Test that root endpoint redirects to static index.html."""
        # Arrange - No special setup needed

        # Act
        response = client.get("/", follow_redirects=False)

        # Assert
        assert response.status_code == 307  # Temporary redirect
        assert response.headers["location"] == "/static/index.html"


class TestActivityDataIntegrity:
    """Test cases to ensure activity data integrity across operations."""

    def test_signup_remove_roundtrip(self, client, reset_activities):
        """Test that signup followed by remove returns to original state."""
        # Arrange
        activity_name = "Programming Class"
        test_email = "roundtrip@mergington.edu"

        original_participants = activities[activity_name]["participants"].copy()

        # Act - Signup
        signup_response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": test_email}
        )

        # Assert signup
        assert signup_response.status_code == 200
        assert test_email in activities[activity_name]["participants"]

        # Act - Remove
        remove_response = client.delete(
            f"/activities/{activity_name}/participant",
            params={"email": test_email}
        )

        # Assert remove
        assert remove_response.status_code == 200
        assert test_email not in activities[activity_name]["participants"]

        # Assert roundtrip - back to original state
        assert activities[activity_name]["participants"] == original_participants

    def test_multiple_signups_different_activities(self, client, reset_activities):
        """Test signing up for multiple different activities."""
        # Arrange
        test_email = "multi@mergington.edu"
        activities_to_join = ["Gym Class", "Tennis Club"]

        # Act & Assert
        for activity_name in activities_to_join:
            response = client.post(
                f"/activities/{activity_name}/signup",
                params={"email": test_email}
            )

            assert response.status_code == 200
            assert test_email in activities[activity_name]["participants"]