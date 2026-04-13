import pytest
from fastapi.testclient import TestClient

from src.app import app, activities

# Copy original activities data for resetting between tests
original_activities = activities.copy()


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset the global activities dictionary before each test to ensure isolation."""
    activities.clear()
    activities.update(original_activities)


client = TestClient(app)


def test_get_activities():
    """Test GET /activities returns all activities with correct structure."""
    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert "Chess Club" in data
    assert "Programming Class" in data
    assert len(data) == 9  # All activities present

    # Check structure of one activity
    chess_club = data["Chess Club"]
    assert "description" in chess_club
    assert "schedule" in chess_club
    assert "max_participants" in chess_club
    assert "participants" in chess_club
    assert isinstance(chess_club["participants"], list)


def test_signup_success():
    """Test successful signup for an activity."""
    # Arrange
    email = "newstudent@mergington.edu"
    activity = "Chess Club"

    # Act
    response = client.post(f"/activities/{activity}/signup?email={email}")

    # Assert
    assert response.status_code == 200
    result = response.json()
    assert "message" in result
    assert email in result["message"]

    # Verify participant was added
    response2 = client.get("/activities")
    data = response2.json()
    assert email in data[activity]["participants"]


def test_signup_duplicate():
    """Test signing up for the same activity twice fails."""
    # Arrange
    email = "duplicatestudent@mergington.edu"
    activity = "Chess Club"
    client.post(f"/activities/{activity}/signup?email={email}")  # First signup

    # Act
    response = client.post(f"/activities/{activity}/signup?email={email}")  # Duplicate

    # Assert
    assert response.status_code == 400
    result = response.json()
    assert "detail" in result
    assert "already signed up" in result["detail"]


def test_signup_activity_full():
    """Test signing up when activity is at capacity fails."""
    # Arrange
    activity = "Chess Club"
    max_participants = activities[activity]["max_participants"]
    # Fill the activity
    for i in range(max_participants - len(activities[activity]["participants"])):
        email = f"fill{i}@mergington.edu"
        client.post(f"/activities/{activity}/signup?email={email}")

    # Act - try to add one more
    response = client.post(f"/activities/{activity}/signup?email=overflow@mergington.edu")

    # Assert
    assert response.status_code == 400
    result = response.json()
    assert "detail" in result
    assert "full" in result["detail"]


def test_signup_activity_not_found():
    """Test signing up for non-existent activity fails."""
    # Arrange
    email = "test@mergington.edu"
    activity = "NonExistent Activity"

    # Act
    response = client.post(f"/activities/{activity}/signup?email={email}")

    # Assert
    assert response.status_code == 404
    result = response.json()
    assert "detail" in result
    assert "not found" in result["detail"]


def test_unregister_success():
    """Test successful unregister from an activity."""
    # Arrange
    email = "unregstudent@mergington.edu"
    activity = "Programming Class"
    client.post(f"/activities/{activity}/signup?email={email}")  # Signup first

    # Act
    response = client.delete(f"/activities/{activity}/unregister?email={email}")

    # Assert
    assert response.status_code == 200
    result = response.json()
    assert "message" in result
    assert "Unregistered" in result["message"]

    # Verify participant was removed
    response2 = client.get("/activities")
    data = response2.json()
    assert email not in data[activity]["participants"]


def test_unregister_not_signed_up():
    """Test unregistering when not signed up fails."""
    # Arrange
    email = "notsigned@mergington.edu"
    activity = "Programming Class"

    # Act
    response = client.delete(f"/activities/{activity}/unregister?email={email}")

    # Assert
    assert response.status_code == 400
    result = response.json()
    assert "detail" in result
    assert "not signed up" in result["detail"]


def test_unregister_activity_not_found():
    """Test unregistering from non-existent activity fails."""
    # Arrange
    email = "test@mergington.edu"
    activity = "NonExistent Activity"

    # Act
    response = client.delete(f"/activities/{activity}/unregister?email={email}")

    # Assert
    assert response.status_code == 404
    result = response.json()
    assert "detail" in result
    assert "not found" in result["detail"]