"""
Test cases for the Mergington High School Activities API
"""

import pytest


class TestRootEndpoint:
    """Tests for the root endpoint"""
    
    def test_root_redirect(self, client):
        """Test that root redirects to /static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivitiesEndpoint:
    """Tests for the GET /activities endpoint"""
    
    def test_get_all_activities(self, client):
        """Test that we can retrieve all activities"""
        response = client.get("/activities")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check that all expected activities are present
        expected_activities = [
            "Chess Club", "Programming Class", "Gym Class", 
            "Basketball Team", "Tennis Club", "Debate Club", 
            "Science Club", "Drama Club", "Art Studio"
        ]
        for activity in expected_activities:
            assert activity in data
    
    def test_activity_structure(self, client):
        """Test that activities have the correct structure"""
        response = client.get("/activities")
        data = response.json()
        
        # Check one activity has all required fields
        chess_club = data["Chess Club"]
        assert "description" in chess_club
        assert "schedule" in chess_club
        assert "max_participants" in chess_club
        assert "participants" in chess_club
        assert isinstance(chess_club["participants"], list)
    
    def test_activities_have_participants(self, client):
        """Test that activities include their participants"""
        response = client.get("/activities")
        data = response.json()
        
        # Chess Club should have michael and daniel
        chess_participants = data["Chess Club"]["participants"]
        assert "michael@mergington.edu" in chess_participants
        assert "daniel@mergington.edu" in chess_participants


class TestSignupEndpoint:
    """Tests for the POST /activities/{activity_name}/signup endpoint"""
    
    def test_successful_signup(self, client):
        """Test that a student can successfully sign up for an activity"""
        response = client.post(
            "/activities/Chess%20Club/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]
    
    def test_signup_adds_participant(self, client):
        """Test that signup actually adds the participant to the activity"""
        # Sign up a new student
        client.post(
            "/activities/Chess%20Club/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        
        # Verify they were added
        response = client.get("/activities")
        participants = response.json()["Chess Club"]["participants"]
        assert "newstudent@mergington.edu" in participants
    
    def test_signup_nonexistent_activity(self, client):
        """Test that signup fails for a non-existent activity"""
        response = client.post(
            "/activities/Fake%20Activity/signup",
            params={"email": "student@mergington.edu"}
        )
        
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_signup_duplicate_student(self, client):
        """Test that a student cannot sign up twice for the same activity"""
        response = client.post(
            "/activities/Chess%20Club/signup",
            params={"email": "michael@mergington.edu"}
        )
        
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]
    
    def test_signup_activity_full(self, client):
        """Test that signup fails when activity is at max capacity"""
        # Tennis Club has max 10 participants and currently has 2
        # Add 8 more to fill it up
        for i in range(8):
            client.post(
                "/activities/Tennis%20Club/signup",
                params={"email": f"student{i}@mergington.edu"}
            )
        
        # Try to sign up one more (should fail)
        response = client.post(
            "/activities/Tennis%20Club/signup",
            params={"email": "overflow@mergington.edu"}
        )
        
        assert response.status_code == 400
        assert "full" in response.json()["detail"]
    
    def test_signup_with_special_characters_in_name(self, client):
        """Test signup for activity with spaces and special characters"""
        response = client.post(
            "/activities/Programming%20Class/signup",
            params={"email": "student@mergington.edu"}
        )
        
        assert response.status_code == 200
    
    def test_signup_email_validation(self, client):
        """Test that various email formats are accepted"""
        # Note: FastAPI doesn't validate email format in query params by default
        response = client.post(
            "/activities/Chess%20Club/signup",
            params={"email": "test.email+tag@mergington.edu"}
        )
        
        # Should succeed as the endpoint doesn't validate email format
        assert response.status_code == 200


class TestIntegration:
    """Integration tests combining multiple endpoints"""
    
    def test_signup_and_verify_participants_updated(self, client):
        """Test the complete flow of signing up and verifying the change"""
        new_email = "integration@mergington.edu"
        
        # Get initial participant count
        response1 = client.get("/activities")
        initial_count = len(response1.json()["Drama Club"]["participants"])
        
        # Sign up
        signup_response = client.post(
            "/activities/Drama%20Club/signup",
            params={"email": new_email}
        )
        assert signup_response.status_code == 200
        
        # Verify the count increased
        response2 = client.get("/activities")
        final_count = len(response2.json()["Drama Club"]["participants"])
        assert final_count == initial_count + 1
    
    def test_multiple_signups(self, client):
        """Test that multiple students can sign up for different activities"""
        emails = ["student1@mergington.edu", "student2@mergington.edu", "student3@mergington.edu"]
        activities = ["Chess Club", "Programming Class", "Science Club"]
        
        for email, activity in zip(emails, activities):
            response = client.post(
                f"/activities/{activity.replace(' ', '%20')}/signup",
                params={"email": email}
            )
            assert response.status_code == 200
        
        # Verify all signups were successful
        response = client.get("/activities")
        data = response.json()
        assert "student1@mergington.edu" in data["Chess Club"]["participants"]
        assert "student2@mergington.edu" in data["Programming Class"]["participants"]
        assert "student3@mergington.edu" in data["Science Club"]["participants"]
