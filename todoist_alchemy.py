"""
todoist_alchemy.py

A proof-of-concept library that treats Todoist as a storage layer,
with minimal "ORM-like" patterns.
"""

import os
import requests
from typing import List, Optional, Union

TODOIST_API_BASE = "https://api.todoist.com/rest/v2/"

class TodoistAlchemyError(Exception):
    """Custom exception for TodoistAlchemy errors."""
    pass

class TodoistAlchemy:
    """
    Manages the connection to Todoist and orchestrates queries/updates.
    Similar concept to a 'Session' in SQLAlchemy.
    """
    def __init__(self, api_token: Optional[str] = None):
        # If no token passed, try environment variable
        self.api_token = api_token or os.environ.get("TODOIST_API_TOKEN")
        if not self.api_token:
            raise TodoistAlchemyError("No Todoist API token provided.")

        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
        
        # Local caches for data (in a real ORM, you'd have more robust tracking)
        self._projects = []
        self._tasks = []
        self._loaded = False
    
    def sync(self):
        """
        Pulls down all relevant data from Todoist and stores locally.
        This is akin to a session "refresh" in an ORM.
        """
        # Get projects
        resp_projects = requests.get(TODOIST_API_BASE + "projects", headers=self.headers)
        if resp_projects.status_code == 200:
            self._projects = resp_projects.json()
        else:
            raise TodoistAlchemyError(f"Error fetching projects: {resp_projects.text}")
        
        # Get tasks
        resp_tasks = requests.get(TODOIST_API_BASE + "tasks", headers=self.headers)
        if resp_tasks.status_code == 200:
            self._tasks = resp_tasks.json()
        else:
            raise TodoistAlchemyError(f"Error fetching tasks: {resp_tasks.text}")
        
        self._loaded = True

    def commit(self):
        """
        In a real ORM, this might flush changes. Here, we only have direct calls
        to the Todoist API for create/update/delete, so there's not much to "commit"
        unless we implement a staging approach.
        """
        pass  # For now, each CRUD operation is immediate (see below)

    # --------------------------------------------------------------------------
    # "Project" operations
    # --------------------------------------------------------------------------
    
    def get_projects(self) -> List[dict]:
        """
        Return the list of project objects currently cached.
        Make sure to call sync() first or rely on an auto-sync approach.
        """
        if not self._loaded:
            self.sync()
        return self._projects

    def create_project(self, name: str) -> dict:
        """
        Create a new project in Todoist, then return the resulting project object.
        """
        payload = {"name": name}
        resp = requests.post(TODOIST_API_BASE + "projects", json=payload, headers=self.headers)
        if resp.status_code == 200:
            project = resp.json()
            self._projects.append(project)
            return project
        else:
            raise TodoistAlchemyError(f"Error creating project: {resp.text}")

    def delete_project(self, project_id: str):
        """
        Delete a project from Todoist.
        """
        resp = requests.delete(TODOIST_API_BASE + f"projects/{project_id}", headers=self.headers)
        if resp.status_code in (204, 200):
            # Remove local reference
            self._projects = [p for p in self._projects if str(p["id"]) != str(project_id)]
        else:
            raise TodoistAlchemyError(f"Error deleting project: {resp.text}")

    # --------------------------------------------------------------------------
    # "Task" operations
    # --------------------------------------------------------------------------

    def get_tasks(self, project_id: Optional[str] = None) -> List[dict]:
        """
        Return the list of task objects. Optionally filter by project.
        """
        if not self._loaded:
            self.sync()
        
        if project_id:
            return [t for t in self._tasks if str(t.get("project_id")) == str(project_id)]
        return self._tasks

    def create_task(self, content: str, project_id: Optional[str] = None, **kwargs) -> dict:
        """
        Create a new task. 'content' is the task name. You can pass other Todoist 
        fields (e.g. 'description', 'due_string', etc.) as kwargs.
        """
        payload = {"content": content}
        if project_id:
            payload["project_id"] = project_id
        # Merge additional fields from kwargs
        payload.update(kwargs)

        resp = requests.post(TODOIST_API_BASE + "tasks", json=payload, headers=self.headers)
        if resp.status_code == 200:
            new_task = resp.json()
            self._tasks.append(new_task)
            return new_task
        else:
            raise TodoistAlchemyError(f"Error creating task: {resp.text}")

    def update_task(self, task_id: Union[str, int], **kwargs) -> dict:
        """
        Update an existing task. Pass fields to change as kwargs.
        """
        resp = requests.post(
            TODOIST_API_BASE + f"tasks/{task_id}",
            json=kwargs,
            headers=self.headers
        )
        if resp.status_code in (204, 200):
            # The API might return 204 with no content. We'll do a new GET:
            updated = requests.get(TODOIST_API_BASE + f"tasks/{task_id}", headers=self.headers)
            if updated.status_code == 200:
                # Update local cache
                updated_task = updated.json()
                for i, t in enumerate(self._tasks):
                    if str(t["id"]) == str(task_id):
                        self._tasks[i] = updated_task
                        break
                return updated_task
            else:
                raise TodoistAlchemyError(f"Error fetching updated task: {updated.text}")
        else:
            raise TodoistAlchemyError(f"Error updating task: {resp.text}")

    def delete_task(self, task_id: Union[str, int]):
        """
        Delete a task from Todoist.
        """
        resp = requests.delete(TODOIST_API_BASE + f"tasks/{task_id}", headers=self.headers)
        if resp.status_code in (204, 200):
            self._tasks = [t for t in self._tasks if str(t["id"]) != str(task_id)]
        else:
            raise TodoistAlchemyError(f"Error deleting task: {resp.text}")
