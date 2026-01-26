from fastapi import APIRouter, HTTPException
from uuid import UUID
from application.use_cases.post_offices.post_office_service import PostOfficeService
from infrastructure.database.post_offices.supabase_post_office_repository import SupabasePostOfficeRepository
from application.dto.post_office_dto import PostOfficeCreateDTO, PostOfficeResponseDTO

router = APIRouter(prefix="/api/v1/post_offices", tags=["Post Offices"])

service = PostOfficeService(SupabasePostOfficeRepository())

@router.get("/{post_office_id}", response_model=PostOfficeResponseDTO)
def get_post_office(post_office_id: UUID):
    try:
        return service.get_post_office_by_id(post_office_id)  
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
@router.get("/area/{area_code}", response_model=list[PostOfficeResponseDTO])
def get_post_offices_by_area_code(area_code: str):
    return service.get_post_offices_by_area_code(area_code)

@router.post("/", response_model=PostOfficeResponseDTO)
def create_post_office(post_office_data: PostOfficeCreateDTO):
    return service.create_post_office(post_office_data)

@router.patch("/{post_office_id}/status")
def update_post_office_status(post_office_id: UUID, status: str):
    try:
        service.update_post_office_status(post_office_id, status)
        return {"message": "Status updated successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

