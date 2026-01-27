from fastapi import APIRouter, HTTPException
from uuid import UUID
from application.use_cases.post_offices.post_office_service import PostOfficeService
from infrastructure.database.post_offices.supabase_post_office_repository import SupabasePostOfficeRepository
from application.dto.post_office_dto import PostOfficeCreateDTO, PostOfficeResponseDTO

post_office_router = APIRouter(prefix="/api/v1/post_offices", tags=["Post Offices"])

service = PostOfficeService(SupabasePostOfficeRepository())

@post_office_router.get("/{post_office_id}", response_model=PostOfficeResponseDTO)
def get_post_office(post_office_id: UUID):
    try:
        return service.get_post_office_by_id(post_office_id)  
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
@post_office_router.get("/area/{area_code}", response_model=list[PostOfficeResponseDTO])
def get_post_offices_by_area_code(area_code: str):
    return service.get_post_offices_by_area_code(area_code)

@post_office_router.post("/", response_model=PostOfficeResponseDTO)
def create_post_office(post_office_data: PostOfficeCreateDTO):
    return service.create_post_office(post_office_data)

@post_office_router.patch("/{post_office_id}/status/activate")
def activate_post_office_status(post_office_id: UUID):
    try:
        service.activate_post_office(post_office_id)
        return {"message": "Status updated successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@post_office_router.patch("/{post_office_id}/status/deactivate")
def deactivate_post_office(post_office_id: UUID):
    try:
        service.deactivate_post_office(post_office_id)
        return {"message": "Status updated successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

