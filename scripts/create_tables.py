# scripts/create_tables.py
#
# Simple database table creation script for development.
#
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Update sys.path to find buro module
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

async def seed_sample_data():
    """Seed the database with sample data."""
    from buro.models import User, Project, Issue, Role, IssueType, IssueStatus, Priority
    from buro.core.database import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        try:
            # Create sample users with short passwords
            admin = User(
                email="admin@buro.dev",
                full_name="System Admin",
                role=Role.ADMIN
            )
            admin.hashed_password = User.hash_password("admin")

            manager = User(
                email="manager@buro.dev",
                full_name="Project Manager",
                role=Role.MANAGER
            )
            manager.hashed_password = User.hash_password("mgr")

            dev1 = User(
                email="developer1@buro.dev",
                full_name="Alice Developer",
                role=Role.DEVELOPER
            )
            dev1.hashed_password = User.hash_password("dev1")

            dev2 = User(
                email="developer2@buro.dev",
                full_name="Bob Developer",
                role=Role.DEVELOPER
            )
            dev2.hashed_password = User.hash_password("dev2")

            users = [admin, manager, dev1, dev2]
            session.add_all(users)
            await session.commit()

            # Create sample project
            project = Project(
                name="Sample Project",
                key="SAMPLE",
                description="A sample project demonstrating agile workflow",
                owner_id=admin.id,
                default_assignee_id=dev1.id
            )
            session.add(project)
            await session.commit()

            # Create sample issues
            issues = [
                Issue(
                    project_id=project.id,
                    reporter_id=admin.id,
                    assignee_id=dev1.id,
                    issue_number=1,
                    title="Implement user authentication system",
                    description="Create JWT-based authentication with role management",
                    issue_type=IssueType.STORY,
                    status=IssueStatus.IN_PROGRESS,
                    priority=Priority.HIGH
                ),
                Issue(
                    project_id=project.id,
                    reporter_id=manager.id,
                    assignee_id=dev2.id,
                    issue_number=2,
                    title="Add Kanban board functionality",
                    description="Implement drag-and-drop issue status transitions",
                    issue_type=IssueType.STORY,
                    status=IssueStatus.TO_DO,
                    priority=Priority.MEDIUM
                ),
                Issue(
                    project_id=project.id,
                    reporter_id=dev1.id,
                    issue_number=3,
                    title="Fix login form validation",
                    description="Email validation not working in Firefox",
                    issue_type=IssueType.BUG,
                    status=IssueStatus.BACKLOG,
                    priority=Priority.HIGH
                )
            ]

            session.add_all(issues)
            await session.commit()

            print("✅ Sample data seeded successfully!")
            print("📝 Sample login credentials:")
            print("   admin@buro.dev / admin (Admin)")
            print("   manager@buro.dev / mgr (Manager)")
            print("   developer1@buro.dev / dev1 (Developer)")
            print("   developer2@buro.dev / dev2 (Developer)")
            return True

        except Exception as e:
            print(f"❌ Failed to seed sample data: {e}")
            await session.rollback()
            return False

async def create_tables():
    """Create all database tables asynchronously."""
    from sqlalchemy import text
    from buro.core.database import engine
    from buro.models import Base

    print("🔧 Creating database tables...")

    try:
        # Create tables using SQLAlchemy metadata
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        print("✅ Tables created successfully!")
        return True
    except Exception as e:
        print(f"❌ Failed to create tables: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import asyncio
    async def main():
        tables_created = await create_tables()
        if tables_created:
            await seed_sample_data()
    asyncio.run(main())