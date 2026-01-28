from fastapi import APIRouter, HTTPException
from uuid import UUID
from application.use_cases.driver.driver_service import DriverService
from infrastructure.database.driver.supabase_driver_repository import SupabaseDriverRepository
from application.dto.driver_dto import DriverDTO, DriverResponseDTO, DriverUpdateDTO

driver_router = APIRouter(prefix="/api/v1/drivers", tags=["Drivers"])
service = DriverService(SupabaseDriverRepository())

@driver_router.get("/{driver_id}",response_model=DriverResponseDTO)
def get_driver(driver_id:UUID):
    try:
        return service.get_driver_by_id(driver_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@driver_router.get("/post_office/{post_office_id}", response_model=list[DriverResponseDTO])
def get_drivers_by_post_office_id(post_office_id:UUID):
    try:
        return service.get_drivers_by_post_office_id(post_office_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@driver_router.get("/status/{status}",response_model=list[DriverResponseDTO])
def get_drivers_by_status(status: str):
    try:
        return service.get_drivers_by_status(status)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@driver_router.post("/", response_model=DriverResponseDTO) 
def create_driver(driver_data: DriverDTO):
    try:
        return service.create_driver(driver_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@driver_router.patch("/{driver_id}", response_model=DriverResponseDTO)
def update_driver(driver_id:UUID, driver_data:DriverUpdateDTO):
    try:
        return service.update_driver(driver_id,driver_data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@driver_router.patch("/{driver_id}/available")
def update_driver_available(driver_id: UUID):
    try:
        return service.available_driver(driver_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@driver_router.patch("/{driver_id}/busy")
def update_driver_busy(driver_id: UUID):
    try:
        return service.busy_driver(driver_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@driver_router.patch("/{driver_id}/inactive")
def update_driver_inactive(driver_id: UUID):
    try:
        return service.inactive_driver(driver_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@driver_router.patch("/{driver_id}/off_duty")
def update_driver_off_duty(driver_id: UUID):
    try:
        return service.off_duty_driver(driver_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
