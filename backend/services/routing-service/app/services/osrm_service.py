import requests
from typing import List, Tuple
from core.config import settings
from core.logger import logger

class OSRMService:
    def __init__(self):
        self.base_url=settings.OSRM_BASE_URL

    def get_distance_matrix(
            self,
            locations:List[Tuple[float,float]]
    )-> List[List[float]]:
        "lấy ma trận khoảnh cách từ osrm location: [(lat, lon),(lat, lon),...]"

        coords=";".join([f"{lon},{lat}" for lat,lon in locations])
        url=f"{self.base_url}/table/v1/driving/{coords}"
        params ={
            "annotations":"distance"
        }
        try:
            response=requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data=response.json()
            if data['code'] !='Ok':
                raise Exception(f"OSRM error: {data['code']}")
            
            distances=data['distances']
            durations = data['durations']
            return distances, durations
        
        except Exception as e:
            logger.error(f"Error fetching distance matrix from OSRM: {e}")
            raise
    
    def get_route(self, locations:List[Tuple[float, float]])->dict:
        "lấy tuyến đường từ osrm location: [(lat, lon),(lat, lon),...]"
        coords=";".join([f"{lon},{lat}" for lat,lon in locations])
        url=f"{self.base_url}/route/v1/driving/{coords}"
        params={
            "overview":"full",
            "geometries":"geojson",
            "steps":"false"
        }
        try:
            response=requests,get(url, params=params, timeout=30)
            response.raise_for_status()
            data=response.json()
            if data['code'] !='Ok':
                raise Exception(f"OSRM error: {data['code']}")
            route=data['routes'][0]

            return {
                "distance": route['distance']/1000,  # km
                "duration": route['duration'],  # giây
                "geometry": route['geometry']['coordinates']  # [[lng, lat], ...]
            }
        except Exception as e:
            logger.error(f"Error fetching route from OSRM: {e}")
            raise
osrm_service=OSRMService()