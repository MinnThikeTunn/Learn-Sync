import logging
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, Field

from backend.app.schemas.course import CourseCreate

logger = logging.getLogger(__name__)


class ProvisioningStepType(str, Enum):
    CREATE_COURSE = "create_course"
    CREATE_ROOT_FOLDER = "create_root_folder"
    SCAFFOLD_SUBFOLDERS = "scaffold_subfolders"


class ProvisioningStep(BaseModel):
    step_type: ProvisioningStepType
    payload: Dict[str, Any]
    description: str
    required: bool = True


class CourseProvisioningPlan(BaseModel):
    user_id: UUID
    course_code: str
    steps: List[ProvisioningStep] = Field(default_factory=list)


class CourseProvisioningPlanner:
    """
    Planner for Course & Virtual Folder Resource Provisioning.
    Pure domain logic: analyzes inputs, determines hierarchy and dependencies,
    and produces an immutable CourseProvisioningPlan.
    """

    def plan(
        self,
        user_id: UUID,
        course: CourseCreate,
    ) -> CourseProvisioningPlan:
        steps = [
            ProvisioningStep(
                step_type=ProvisioningStepType.CREATE_COURSE,
                payload={
                    "name": course.name.strip(),
                    "code": course.code.strip(),
                    "term": course.term.strip() if course.term else None,
                    "color": course.color or "#3b82f6",
                    "description": course.description.strip() if course.description else None,
                },
                description=f"Create course record '{course.name}' ({course.code})",
                required=True,
            ),
            ProvisioningStep(
                step_type=ProvisioningStepType.CREATE_ROOT_FOLDER,
                payload={
                    "name": course.code.strip(),
                    "parent_id": None,
                    "parent_path": "",
                    "parent_depth": 0,
                },
                description=f"Provision root virtual folder for course '{course.code}'",
                required=False,  # Root folder creation failure should not fail course creation
            ),
        ]

        return CourseProvisioningPlan(
            user_id=user_id,
            course_code=course.code.strip(),
            steps=steps,
        )


class CourseProvisioningResult(BaseModel):
    status: str = "success"  # "success", "partial_success", "failed"
    course: Optional[Dict[str, Any]] = None
    root_folder: Optional[Dict[str, Any]] = None
    executed_steps: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)


class CourseProvisioningExecutor:
    """
    Executor for Course & Virtual Folder Resource Provisioning.
    Executes provisioning plans against the persistence layer (DatabaseService),
    tracking step execution, logging anomalies, and isolating non-critical failures.
    """

    def __init__(self, db_service: Any = None):
        if db_service is None:
            from backend.app.services.database import db_service as default_db
            self.db_service = default_db
        else:
            self.db_service = db_service

    def execute(self, plan: CourseProvisioningPlan) -> CourseProvisioningResult:
        result = CourseProvisioningResult()
        created_course_id = None

        for step in plan.steps:
            if step.step_type == ProvisioningStepType.CREATE_COURSE:
                try:
                    course_record = self.db_service.create_course(
                        user_id=plan.user_id,
                        name=step.payload["name"],
                        code=step.payload["code"],
                        term=step.payload.get("term"),
                        color=step.payload.get("color"),
                        description=step.payload.get("description"),
                    )
                    result.course = course_record
                    result.executed_steps.append(step.description)
                    created_course_id = course_record.get("id") if isinstance(course_record, dict) else None
                except Exception as e:
                    logger.error(f"Failed to execute step {step.step_type}: {e}")
                    result.errors.append(f"Failed to create course: {str(e)}")
                    if step.required:
                        result.status = "failed"
                        return result

            elif step.step_type == ProvisioningStepType.CREATE_ROOT_FOLDER:
                if not created_course_id:
                    result.errors.append("Cannot provision root virtual folder: course_id is missing.")
                    continue

                try:
                    folder_record = self.db_service.create_virtual_folder(
                        user_id=plan.user_id,
                        course_id=str(created_course_id),
                        name=step.payload["name"],
                        parent_id=step.payload.get("parent_id"),
                        parent_path=step.payload.get("parent_path", ""),
                        parent_depth=step.payload.get("parent_depth", 0),
                    )
                    result.root_folder = folder_record
                    result.executed_steps.append(step.description)
                except Exception as e:
                    logger.warning(f"Failed non-critical step {step.step_type}: {e}")
                    result.errors.append(f"Root folder provisioning failed: {str(e)}")
                    if result.status == "success":
                        result.status = "partial_success"

        return result

