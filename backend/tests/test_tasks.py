

class TestCreateTask:
    """Tests for POST /tasks"""

    def test_create_task_success(self, client, auth_headers):
        response = client.post(
            "/tasks/", 
            json={
                "title": "Clean",
                "description": "Clean my room monday",
                "priority": "low",
                "completed": False,
            },
            headers = auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Clean"
        assert "id" in data
        assert "created_at" in data 


    def test_create_task_missing_title(self, client, auth_headers):
        response = client.post(
            "/tasks/", 
            json={
                "description": "Clean my room monday",
                "priority": "low",
                "completed": False,
            },
            headers = auth_headers,
        )
        assert response.status_code == 422


    
    def test_unauthorized_access(self, client):
        response = client.post(
            "/tasks/", 
            json={
                "title": "Clean",
                "description": "Clean my room monday",
                "priority": "low",
                "completed": False,
            },
        )
        assert response.status_code == 401






class TestListTask:
    """Tests for GET /tasks """

    def test_list_with_data(self, client, sample_task, auth_headers):
        response = client.get(
            "/tasks/", 
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()

        titles = [task["title"] for task in data]
        assert "Clean" in titles
        assert len(data) == 1




class TestReadTasks:
    """Tests for GET /tasks/{id}"""

    def test_get_task_by_id(self, client, sample_task, auth_headers):
        response = client.get(
            f"/tasks/{sample_task['id']}", 
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["title"] == "Clean"

    def test_get_task_not_found(self, client, auth_headers):
        response = client.get("/tasks/9999", headers=auth_headers)
        assert response.status_code == 404




class TestUpdateTask:
    """Tests for PATCH /tasks/{id}"""

    def test_patch_task_title(self, client, sample_task, auth_headers):
        response = client.patch(
            f"/tasks/{sample_task['id']}", 
            json={"title": "Updated Title"}, 
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["title"] == "Updated Title"
        assert response.json()["description"] == "Clean my room monday"




class TestDeleteTask:
    """Tests for DELETE /tasks/{id}"""

    def test_delete_task(self, client, sample_task, auth_headers):
        response = client.delete(
            f"/tasks/{sample_task['id']}", 
            headers=auth_headers
        )
        assert response.status_code == 204

        # verify that it's gone 
        response = client.get(f"/tasks/{sample_task['id']}", headers=auth_headers)
        assert response.status_code == 404







