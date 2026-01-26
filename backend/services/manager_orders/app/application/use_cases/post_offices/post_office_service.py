from typing import List
from uuid import UUID
from domain.entities.post_offices.post_office import PostOffice
from domain.repositories.post_office_repository import PostOfficeRepository

class PostOfficeService:
    def __init__(self, repository: PostOfficeRepository):
        self.repository = repository

    def get_post_office_by_id(self, post_office_id: UUID) -> PostOffice:
        post_office = self.repository.get_by_id(post_office_id)
        if not post_office:
            raise ValueError(f"Post office with ID {post_office_id} not found")
        return post_office

    def get_post_offices_by_area_code(self, area_code: str) -> List[PostOffice]:
        return self.repository.get_by_area_code(area_code)

    def create_post_office(self, post_office_data) -> PostOffice:
        # Convert DTO to Entity
        post_office = PostOffice(
            id=None,  # Sẽ được Supabase tự generate
            code=post_office_data.code,
            name=post_office_data.name,
            address=post_office_data.address,
            ward=post_office_data.ward,
            district=post_office_data.district,
            province=post_office_data.province,
            area_codes=post_office_data.area_codes,
            phone=post_office_data.phone,
            email=post_office_data.email,
            open_time=post_office_data.open_time,
            close_time=post_office_data.close_time,
            working_days=post_office_data.working_days,
            manager_id=post_office_data.manager_id,
            status=post_office_data.status,
            location=post_office_data.location
        )
        return self.repository.create(post_office)

    def activate_post_office(self, post_office_id: UUID) -> None:
        self.repository.update(post_office_id, status="active")

    def deactivate_post_office(self, post_office_id: UUID) -> None:
        self.repository.update(post_office_id, status="inactive")