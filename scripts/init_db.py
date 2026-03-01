# scripts/init_db.py
#
# Database initialization script for setting up Buro's PostgreSQL database.
#
# Educational Notes for Junior Developers:
# - Alembic vs. Direct SQLAlchemy: Alembic provides version control for schemas,
#   enabling safe forward/backward migrations in production.
# - Why separate init script: Allows database setup without starting the full app.
# - Environment handling: Uses .env for configuration isolation.
#   Never hardcode database credentials!

import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv

# Why import at function level: Avoids circular imports and optional dependencies
# Tradeoff: Cannot use these globally vs. lazy loading for optional operations

async def create_tables():
    """Create all database tables asynchronously.

    Educational Note: Async database operations in initialization.
    - Benefits: Non-blocking during startup
    - Why needed: SQLAlchemy tables creation with async engine
    """
    from sqlalchemy import text
    from buro.core.database import engine
    from buro.models import Base

    print("🔧 Creating database tables...")

    try:
        # Create tables using SQLAlchemy metadata
        # Why async with engine.begin(): Commits transactions automatically
        # Alternative: manual transaction handling (error-prone)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        print("✅ Tables created successfully!")
        return True
    except Exception as e:
        print(f"❌ Failed to create tables: {e}")
        return False

async def seed_sample_data():
    """Optional sample data for development and testing.

    Why separate function: Allows developers to skip seeding if desired.
    Educational Note: Seeding best practices:
    - Use factories for test data generation
    - Avoid in production (use migrations instead)
    - Include different user roles for testing permissions
    """
    from sqlalchemy.ext.asyncio import AsyncSession
    from buro.core.database import AsyncSessionLocal
    from buro.models import User, Project, Issue, Role, IssueType, IssueStatus, Priority

    print("🌱 Seeding sample data...")

    # Why context manager: Ensures session cleanup even on errors
    async with AsyncSessionLocal() as session:
        try:
            # Create sample users with different roles
            admin = User(
                email="admin@buro.dev",
                full_name="System Admin",
                role=Role.ADMIN
            )
            admin.hashed_password = User.hash_password("admin123")

            manager = User(
                email="manager@buro.dev",
                full_name="Project Manager",
                role=Role.MANAGER
            )
            manager.hashed_password = User.hash_password("manager123")

            dev1 = User(
                email="developer1@buro.dev",
                full_name="Alice Developer",
                role=Role.DEVELOPER
            )
            dev1.hashed_password = User.hash_password("dev123")

            dev2 = User(
                email="developer2@buro.dev",
                full_name="Bob Developer",
                role=Role.DEVELOPER
            )
            dev2.hashed_password = User.hash_password("dev123")

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
                ),
                Issue(
                    project_id=project.id,
                    reporter_id=admin.id,
                    issue_number=4,
                    title="Epic: Database redesign for scale",
                    description="Implement database optimizations for 10-20 issues/month",
                    issue_type=IssueType.EPIC,
                    status=IssueStatus.BACKLOG,
                    priority=Priority.LOW
                )
            ]

            session.add_all(issues)
            await session.commit()

            print("✅ Sample data seeded successfully!")
            print(f"   Users created: {len(users)}")
            print(f"   Projects: 1")
            print(f"   Issues: {len(issues)}")
            print("\n📝 Sample login credentials:")
            print("   admin@buro.dev / admin123 (Admin)")
            print("   manager@buro.dev / manager123 (Manager)")
            print("   developer1@buro.dev / dev123 (Developer)")
            return True

        except Exception as e:
            print(f"❌ Failed to seed sample data: {e}")
            await session.rollback()
            return False

async def main():
    """Main initialization function with user interaction.

    Educational Note: Script patterns for database operations.
    - Configurable actions (tables vs. data seeding)
    - User confirmation for destructive operations
    - Proper error handling and cleanup
    """
    print("🚀 Buro Database Initialization")
    print("="*40)

    # Check environment configuration
    load_dotenv()
    db_url = os.getenv("DATABASE_URL", "")
    if not db_url:
        print("❌ DATABASE_URL not found in environment!")
        print("💡 Copy .env.example to .env and fill in your database credentials")
        return

    print(f"📍 Using database: {db_url}")

    # Ask user what to do
    print("\nWhat would you like to do?")
    print("1. Create tables only")
    print("2. Create tables and seed sample data")

    choice = input("\nEnter choice (1-2): ").strip()

    success = False

    if choice == "1":
        success = await create_tables()
    elif choice == "2":
        success = await create_tables()
        if success:
            success = await seed_sample_data()
    else:
        print("❌ Invalid choice.")
        return

    if success:
        print("\n🎉 Database initialized successfully!")
        print("💡 You can now start the FastAPI server with: uvicorn buro.main:app --reload")
    else:
        print("\n❌ Database initialization failed.")

if __name__ == "__main__":
    # Why asyncio.run(): Execute the async main function
    # For scripts, this provides a clean entry point
    asyncio.run(main())
