# Test script to debug status update issue
import asyncio
import os
from buro.services.issue_service import IssueService
from buro.core.database import AsyncSessionLocal, engine
from buro.models import User, IssueStatus
from buro.api.auth import SECRET_KEY
from sqlalchemy import text

async def test_status_update():
    async with AsyncSessionLocal() as db:
        # Get a user - use the admin user
        result = await db.execute(text("SELECT id FROM users LIMIT 1"))
        user_id = result.scalar()

        if not user_id:
            print("No users found")
            return

        from buro.models import User
        user = await db.get(User, user_id)

        # Get an issue
        result = await db.execute(text("SELECT id FROM issues LIMIT 1"))
        issue_id = result.scalar()

        if not issue_id:
            print("No issues found")
            return

        print(f"Testing status update for issue {issue_id}")

        # Test the service
        service = IssueService(db)
        try:
            updated_issue = await service.transition_issue_status(
                issue_id=issue_id,
                new_status=IssueStatus.DONE,
                current_user=user
            )
            print("✅ Status update succeeded")
            print(f"New status: {updated_issue.status}")

            from buro.api.issues import IssueResponse
            try:
                response = IssueResponse.from_issue(updated_issue)
                print("✅ IssueResponse creation succeeded")
            except Exception as e:
                print(f"❌ IssueResponse creation failed: {e}")
                import traceback
                traceback.print_exc()

        except Exception as e:
            print(f"❌ Status update failed: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_status_update())