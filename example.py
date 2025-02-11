from todoist_alchemy import TodoistAlchemy

def main():
    # Connect (token can come from an env var or explicitly here)
    session = TodoistAlchemy(api_token="YOUR_TODOIST_API_TOKEN")

    # Sync existing data
    session.sync()

    # List all projects
    projects = session.get_projects()
    print("Projects:", projects)

    # Create a new project
    new_proj = session.create_project("My Test Project")
    print("Created project:", new_proj)

    # Create a task in that project
    new_task = session.create_task(
        content="Test Task in My Test Project",
        project_id=new_proj["id"],
        description="This is a test task created via TodoistAlchemy."
    )
    print("Created task:", new_task)

    # Update the task
    updated_task = session.update_task(new_task["id"], content="Renamed Test Task")
    print("Updated task:", updated_task)

    # Delete the task
    session.delete_task(updated_task["id"])
    print("Deleted the task.")

    # Delete the project
    session.delete_project(new_proj["id"])
    print("Deleted the project.")

if __name__ == "__main__":
    main()
