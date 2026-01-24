from typing import List, Tuple
from services.osrm_service import osrm_service
from utils.geo import haversine_distance
from core.logger import logger

class DistanceMatrixService:
    @staticmethod
    def get_matrix(
        locations: List[Tuple[float, float]],
        use_osrm: bool = True
    ) -> Tuple[List[List[float]], List[List[float]]]:
        """
        Lấy ma trận khoảng cách
        locations: [(lng, lat), ...]
        Returns: (distance_matrix, duration_matrix)
        """
        if use_osrm:
            try:
                return osrm_service.get_distance_matrix(locations)
            except Exception as e:
                logger.warning(f"OSRM failed, fallback to Haversine: {e}")
                return DistanceMatrixService._haversine_matrix(locations)
        else:
            return DistanceMatrixService._haversine_matrix(locations)
    
    @staticmethod
    def _haversine_matrix(
        locations: List[Tuple[float, float]]
    ) -> Tuple[List[List[float]], List[List[float]]]:
        """
        Tính ma trận khoảng cách bằng Haversine (fallback)
        """
        n = len(locations)
        distance_matrix = [[0.0] * n for _ in range(n)]
        duration_matrix = [[0.0] * n for _ in range(n)]
        
        for i in range(n):
            for j in range(n):
                if i != j:
                    # lng, lat -> lat, lng
                    dist = haversine_distance(
                        locations[i][1], locations[i][0],
                        locations[j][1], locations[j][0]
                    )
                    distance_matrix[i][j] = dist * 1000  # km -> m
                    # Giả sử tốc độ 40km/h
                    duration_matrix[i][j] = (dist / 40) * 3600
        
        return distance_matrix, duration_matrix

distance_matrix_service = DistanceMatrixService()