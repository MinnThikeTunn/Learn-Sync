import pytest
from uuid import uuid4
from backend.app.schemas.course import CourseCreate
from backend.app.services.course_provisioner import (
    CourseProvisioningPlanner,
    CourseProvisioningPlan,
    ProvisioningStepType,
)


def test_planner_generates_valid_course_and_root_folder_plan():
    """
    Slice 1 (TDD Red):
    The CourseProvisioningPlanner must take a CourseCreate request and user_id,
    and generate a CourseProvisioningPlan with:
    1. A CREATE_COURSE step with normalized course metadata.
    2. A CREATE_ROOT_FOLDER step with normalized folder name and root path parameters.
    """
    user_id = uuid4()
    course_in = CourseCreate(
        name="Distributed Systems",
        code="CS301",
        term="Fall 2026",
        color="#3b82f6",
        description="Consensus, replication, and fault tolerance.",
    )

    planner = CourseProvisioningPlanner()
    plan = planner.plan(user_id=user_id, course=course_in)

    assert isinstance(plan, CourseProvisioningPlan)
    assert plan.user_id == user_id
    assert len(plan.steps) == 2

    # Step 1: Course creation step
    step_course = plan.steps[0]
    assert step_course.step_type == ProvisioningStepType.CREATE_COURSE
    assert step_course.payload["name"] == "Distributed Systems"
    assert step_course.payload["code"] == "CS301"

    # Step 2: Root folder creation step
    step_folder = plan.steps[1]
    assert step_folder.step_type == ProvisioningStepType.CREATE_ROOT_FOLDER
    assert step_folder.payload["name"] == "CS301"
    assert step_folder.payload["parent_path"] == ""
    assert step_folder.payload["parent_depth"] == 0


def test_executor_executes_plan_and_provisions_both_course_and_folder():
    """
    Slice 2 (TDD Red):
    The CourseProvisioningExecutor executes the planned steps via the database repository:
    1. Creates the course record.
    2. Uses the newly generated course_id to provision the root virtual folder.
    3. Returns a CourseProvisioningResult containing both created entities.
    """
    from unittest.mock import MagicMock
    from backend.app.services.course_provisioner import (
        CourseProvisioningExecutor,
        CourseProvisioningResult,
    )

    user_id = uuid4()
    mock_course_id = uuid4()
    mock_folder_id = uuid4()

    mock_db = MagicMock()
    mock_db.create_course.return_value = {
        "id": str(mock_course_id),
        "user_id": str(user_id),
        "name": "Distributed Systems",
        "code": "CS301",
        "term": "Fall 2026",
        "color": "#3b82f6",
        "description": "Consensus, replication, and fault tolerance.",
    }
    mock_db.create_virtual_folder.return_value = {
        "id": str(mock_folder_id),
        "user_id": str(user_id),
        "course_id": str(mock_course_id),
        "name": "CS301",
        "materialized_path": "/CS301",
        "depth": 0,
    }

    course_in = CourseCreate(
        name="Distributed Systems",
        code="CS301",
        term="Fall 2026",
        color="#3b82f6",
        description="Consensus, replication, and fault tolerance.",
    )

    planner = CourseProvisioningPlanner()
    plan = planner.plan(user_id=user_id, course=course_in)

    executor = CourseProvisioningExecutor(db_service=mock_db)
    result = executor.execute(plan)

    assert isinstance(result, CourseProvisioningResult)
    assert result.status == "success"
    assert result.course["id"] == str(mock_course_id)
    assert result.root_folder["id"] == str(mock_folder_id)
    assert len(result.executed_steps) == 2
    assert len(result.errors) == 0

    mock_db.create_course.assert_called_once_with(
        user_id=user_id,
        name="Distributed Systems",
        code="CS301",
        term="Fall 2026",
        color="#3b82f6",
        description="Consensus, replication, and fault tolerance.",
    )
    mock_db.create_virtual_folder.assert_called_once_with(
        user_id=user_id,
        course_id=str(mock_course_id),
        name="CS301",
        parent_id=None,
        parent_path="",
        parent_depth=0,
    )


def test_executor_handles_folder_provisioning_failure_gracefully():
    """
    Slice 3 (TDD):
    If root folder provisioning encounters an exception:
    - The course is still successfully preserved.
    - Status is marked 'partial_success'.
    - The error is captured in result.errors without crashing.
    """
    from unittest.mock import MagicMock
    from backend.app.services.course_provisioner import (
        CourseProvisioningExecutor,
    )

    user_id = uuid4()
    mock_course_id = uuid4()

    mock_db = MagicMock()
    mock_db.create_course.return_value = {
        "id": str(mock_course_id),
        "user_id": str(user_id),
        "name": "Distributed Systems",
        "code": "CS301",
    }
    # Simulate DB error on folder creation
    mock_db.create_virtual_folder.side_effect = RuntimeError("Supabase folder table timeout")

    planner = CourseProvisioningPlanner()
    plan = planner.plan(
        user_id=user_id,
        course=CourseCreate(name="Distributed Systems", code="CS301"),
    )

    executor = CourseProvisioningExecutor(db_service=mock_db)
    result = executor.execute(plan)

    assert result.status == "partial_success"
    assert result.course["id"] == str(mock_course_id)
    assert result.root_folder is None
    assert len(result.errors) == 1
    assert "Root folder provisioning failed" in result.errors[0]


def test_executor_aborts_when_course_creation_fails():
    """
    Slice 3 (TDD):
    If course creation fails:
    - Status is marked 'failed'.
    - Root folder provisioning is never attempted.
    """
    from unittest.mock import MagicMock
    from backend.app.services.course_provisioner import (
        CourseProvisioningExecutor,
    )

    user_id = uuid4()
    mock_db = MagicMock()
    mock_db.create_course.side_effect = ValueError("Duplicate course code")

    planner = CourseProvisioningPlanner()
    plan = planner.plan(
        user_id=user_id,
        course=CourseCreate(name="Distributed Systems", code="CS301"),
    )

    executor = CourseProvisioningExecutor(db_service=mock_db)
    result = executor.execute(plan)

    assert result.status == "failed"
    assert result.course is None
    assert result.root_folder is None
    assert "Failed to create course" in result.errors[0]
    mock_db.create_virtual_folder.assert_not_called()


