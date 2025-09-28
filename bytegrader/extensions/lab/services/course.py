from bytegrader.schemas.course import UpdateCourseRequest
from ..schemas.base import LabAPIResponse
from ....core.utils.hub import HubApiClient
from ....schemas.assignment import AssignmentCreateRequest
from ....schemas.base import APIResponse
from ....schemas.course import CreateCourseRequest


class LabCourseService:

    def __init__(self, hub_client: 'HubApiClient'):
        self.hub_client = hub_client

    async def list_courses(self) -> LabAPIResponse:
        try:
            response = self.hub_client.query_hub_service(
                method='GET',
                api_path='/courses',
                params={}
            )
            return LabAPIResponse.parse_obj(response)
        except Exception as e:
            return LabAPIResponse.error_response(f"Failed to list courses: {str(e)}")

    async def create_course(self, course_data: 'CreateCourseRequest') -> LabAPIResponse:
        try:
            response = self.hub_client.query_hub_service(
                method='POST',
                api_path='/courses/create',
                data=course_data.model_dump(by_alias=True)
            )
            return LabAPIResponse.parse_obj(response)
        except Exception as e:
            return LabAPIResponse.error_response(f"Failed to create course: {str(e)}")

    async def delete_course(self, course_id: str) -> LabAPIResponse:
        try:
            response = self.hub_client.query_hub_service(
                method='DELETE',
                api_path=f'/courses/{course_id}/delete'
            )
            return LabAPIResponse.parse_obj(response)
        except Exception as e:
            return LabAPIResponse.error_response(f"Failed to delete course: {str(e)}")

    async def update_course(self, course_id: str, course_data: 'UpdateCourseRequest') -> LabAPIResponse:
        try:
            response = self.hub_client.query_hub_service(
                method='PATCH',
                api_path=f'/courses/{course_id}/update',
                data=course_data.model_dump(by_alias=True)
            )
            return LabAPIResponse.parse_obj(response)
        except Exception as e:
            return LabAPIResponse.error_response(f"Failed to update course: {str(e)}")