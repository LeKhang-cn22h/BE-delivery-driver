from uuid import UUID
from datetime import datetime, timedelta
from typing import Optional, List, Tuple, Dict
from supabase import Client
import math
from DTO.Location import LocationUpdateDTO, parse_point, to_point_string


class LocationSmoother:
    """
    Thuật toán làm mượt và nén dữ liệu GPS
    
    Strategies:
    1. Douglas-Peucker: Loại bỏ điểm không cần thiết trên đường thẳng
    2. Distance Filter: Chỉ lưu khi di chuyển > threshold
    3. Time Filter: Lưu tối thiểu mỗi X giây
    4. Speed Filter: Loại bỏ điểm có tốc độ bất thường
    """
    
    def __init__(
        self,
        min_distance_meters: float = 10.0,      # Khoảng cách tối thiểu để lưu (mét)
        min_time_seconds: float = 5.0,          # Thời gian tối thiểu giữa 2 điểm (giây)
        max_speed_kmh: float = 120.0,           # Tốc độ tối đa hợp lệ (km/h)
        douglas_peucker_epsilon: float = 0.00005  # Độ chính xác Douglas-Peucker
    ):
        self.min_distance = min_distance_meters
        self.min_time = min_time_seconds
        self.max_speed = max_speed_kmh
        self.epsilon = douglas_peucker_epsilon

        # Cache lưu trạng thái điểm cuối cùng của mỗi driver
        self._last_points: Dict[str, dict] = {}
    
    @staticmethod
    def haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """
        Tính khoảng cách giữa 2 điểm GPS (lat, lng) bằng công thức Haversine
        
        Args:
            lat1, lng1: Tọa độ điểm 1
            lat2, lng2: Tọa độ điểm 2
            
        Returns:
            Khoảng cách tính bằng mét
        """
        R = 6371000  # Bán kính Trái Đất (mét)
        
        # Chuyển đổi độ sang radian
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lng2 - lng1)
        
        # Công thức Haversine
        a = math.sin(delta_phi / 2) ** 2 + \
            math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    @staticmethod
    def calculate_speed(
        lat1: float, lng1: float, time1: datetime,
        lat2: float, lng2: float, time2: datetime
    ) -> float:
        """
        Tính tốc độ di chuyển giữa 2 điểm
        
        Args:
            lat1, lng1, time1: Tọa độ và thời gian điểm 1
            lat2, lng2, time2: Tọa độ và thời gian điểm 2
            
        Returns:
            Tốc độ tính bằng km/h
        """
        distance = LocationSmoother.haversine_distance(lat1, lng1, lat2, lng2)  # mét
        time_diff = (time2 - time1).total_seconds()  # giây

        if time_diff <= 0:
            return 0
        
        speed_ms = distance / time_diff  # m/s
        speed_kmh = speed_ms * 3.6       # km/h
        return speed_kmh
    
    def should_save_point(
        self,
        driver_id: str,  # FIX: Đổi từ UUID sang str để dùng làm key dict
        lat: float,
        lng: float,
        timestamp: datetime,
        speed: Optional[float] = None
    ) -> Tuple[bool, str]:
        """
        Quyết định có nên lưu điểm này vào history không
        
        Args:
            driver_id: ID của driver
            lat, lng: Tọa độ GPS
            timestamp: Thời gian ghi nhận
            speed: Tốc độ từ GPS sensor (nếu có)
            
        Returns:
            Tuple (should_save: bool, reason: str)
        """
        # Chuyển driver_id sang string để dùng làm key
        driver_key = str(driver_id)
        last_point = self._last_points.get(driver_key)

        # Điểm đầu tiên của driver -> luôn lưu
        if not last_point:
            self._last_points[driver_key] = {
                "lat": lat,
                "lng": lng,
                "timestamp": timestamp
            }
            return True, "first_point"

        # Tính khoảng cách từ điểm cuối cùng đã lưu
        distance = self.haversine_distance(
            last_point["lat"], last_point["lng"],
            lat, lng
        )

        # Tính thời gian từ điểm cuối cùng
        time_diff = (timestamp - last_point["timestamp"]).total_seconds()

        # Tính tốc độ dựa trên 2 điểm (để validate)
        calculated_speed = self.calculate_speed(
            last_point["lat"], last_point["lng"], last_point["timestamp"],
            lat, lng, timestamp
        )

        # ===== FILTER 1: Speed Filter =====
        # Kiểm tra tốc độ từ GPS sensor
        if speed is not None and speed > self.max_speed:
            return False, "gps_speed_too_high"
        
        # Kiểm tra tốc độ tính toán (phát hiện GPS jump)
        if calculated_speed > self.max_speed:
            return False, "calculated_speed_too_high"

        # ===== FILTER 2: Distance Filter =====
        # Nếu di chuyển đủ xa -> lưu
        if distance >= self.min_distance:
            self._last_points[driver_key] = {
                "lat": lat,
                "lng": lng,
                "timestamp": timestamp
            }
            return True, "distance_threshold_met"

        # ===== FILTER 3: Time Filter =====
        # Force save nếu quá lâu không lưu (30 giây = min_time * 6)
        if time_diff >= self.min_time * 6:
            self._last_points[driver_key] = {
                "lat": lat,
                "lng": lng,
                "timestamp": timestamp
            }
            return True, "time_threshold_met"

        # Không đạt bất kỳ threshold nào -> không lưu
        return False, "below_all_thresholds"
    
    def clear_driver_cache(self, driver_id: str) -> None:
        """
        Xóa cache của driver (khi driver offline hoặc kết thúc ca)
        
        Args:
            driver_id: ID của driver cần xóa cache
        """
        driver_key = str(driver_id)
        if driver_key in self._last_points:
            del self._last_points[driver_key]
    
    @staticmethod
    def douglas_peucker(points: List[dict], epsilon: float) -> List[dict]:
        """
        Thuật toán Douglas-Peucker để nén dữ liệu tuyến đường
        Giữ lại các điểm quan trọng, loại bỏ điểm trên đường thẳng
        
        Args:
            points: Danh sách điểm, mỗi điểm là dict có 'lat' và 'lng'
            epsilon: Ngưỡng sai số (độ), càng nhỏ càng giữ nhiều điểm
            
        Returns:
            Danh sách điểm đã được nén
        """
        # Cần ít nhất 3 điểm để nén
        if len(points) < 3:
            return points

        # Tìm điểm có khoảng cách lớn nhất từ đoạn thẳng nối 2 đầu
        start = points[0]
        end = points[-1]
        max_dist = 0.0
        max_index = 0

        for i in range(1, len(points) - 1):
            point = points[i]
            dist = LocationSmoother._perpendicular_distance(point, start, end)
            if dist > max_dist:
                max_dist = dist
                max_index = i

        # Nếu khoảng cách lớn hơn epsilon -> đệ quy chia đoạn
        if max_dist > epsilon:
            # Đệ quy xử lý 2 nửa
            left = LocationSmoother.douglas_peucker(points[:max_index + 1], epsilon)
            right = LocationSmoother.douglas_peucker(points[max_index:], epsilon)
            
            # Ghép lại, bỏ điểm trùng ở giữa
            return left[:-1] + right
        else:
            # Đoạn này đủ thẳng -> chỉ giữ 2 đầu
            return [start, end]
    
    @staticmethod
    def _perpendicular_distance(point: dict, start: dict, end: dict) -> float:
        """
        Tính khoảng cách vuông góc từ điểm đến đoạn thẳng
        
        Args:
            point: Điểm cần tính {'lat': float, 'lng': float}
            start: Điểm đầu đoạn thẳng
            end: Điểm cuối đoạn thẳng
            
        Returns:
            Khoảng cách (đơn vị: độ, để so sánh với epsilon)
        """
        # Nếu start == end thì tính khoảng cách trực tiếp
        if start["lat"] == end["lat"] and start["lng"] == end["lng"]:
            return LocationSmoother.haversine_distance(
                point["lat"], point["lng"],
                start["lat"], start["lng"]
            ) / 111000  # Chuyển mét sang độ (xấp xỉ)

        # Tính khoảng cách vuông góc bằng công thức hình học
        # |Ax + By + C| / sqrt(A^2 + B^2)
        # Với đường thẳng qua 2 điểm: (y2-y1)x - (x2-x1)y + x2*y1 - y2*x1 = 0
        
        x1, y1 = start["lat"], start["lng"]
        x2, y2 = end["lat"], end["lng"]
        x0, y0 = point["lat"], point["lng"]
        
        num = abs((y2 - y1) * x0 - (x2 - x1) * y0 + x2 * y1 - y2 * x1)
        den = math.sqrt((y2 - y1) ** 2 + (x2 - x1) ** 2)
        
        if den == 0:
            return 0
            
        return num / den


# ============================================================
# LOCATION SERVICE CLASS
# ============================================================

class LocationService:
    """
    Service xử lý các thao tác liên quan đến vị trí driver
    
    Responsibilities:
    - Cập nhật vị trí hiện tại (real-time)
    - Lưu lịch sử vị trí (với data smoothing)
    - Query lịch sử di chuyển
    - Lấy danh sách drivers đang hoạt động
    """
    
    def __init__(self, supabase: Client):
        self.supabase = supabase
        # Khởi tạo smoother với config mặc định
        self.smoother = LocationSmoother(
            min_distance_meters=10.0,    # Lưu khi di chuyển > 10m
            min_time_seconds=5.0,        # Tối thiểu 5 giây giữa 2 điểm
            max_speed_kmh=120.0,         # Tốc độ tối đa 120 km/h
            douglas_peucker_epsilon=0.00005
        )
    
    # ================== UPDATE LOCATION ==================
    
    def update_current_location(self, driver_id: UUID, location: LocationUpdateDTO) -> dict:
        """
        Cập nhật vị trí hiện tại của driver (UPSERT)
        Luôn cập nhật để hiển thị real-time
        
        Args:
            driver_id: UUID của driver
            location: DTO chứa thông tin vị trí
            
        Returns:
            Dict với updated_at timestamp
        """
        location_point = to_point_string(location.lat, location.lng)
        now = datetime.now().isoformat()
        
        self.supabase.schema("delivery").table("driver_current_locations").upsert({
            "driver_id": str(driver_id),
            "location": location_point,
            "speed": location.speed,
            "heading": location.heading,
            "status": location.status,
            "schedule_id": str(location.schedule_id) if location.schedule_id else None,
            "current_order_detail_id": str(location.order_detail_id) if location.order_detail_id else None,
            "updated_at": now
        }).execute()
        
        return {"updated_at": now}
    
    def save_location_history(self, driver_id: UUID, location: LocationUpdateDTO) -> dict:
        """
        Lưu vị trí vào bảng lịch sử
        
        Args:
            driver_id: UUID của driver
            location: DTO chứa thông tin vị trí
            
        Returns:
            Dict với recorded_at timestamp
        """
        location_point = to_point_string(location.lat, location.lng)
        now = datetime.now().isoformat()
        
        self.supabase.schema("delivery").table("driver_location_history").insert({
            "driver_id": str(driver_id),
            "schedule_id": str(location.schedule_id) if location.schedule_id else None,
            "order_detail_id": str(location.order_detail_id) if location.order_detail_id else None,
            "location": location_point,
            "speed": location.speed,
            "heading": location.heading,
            "status": location.status,
            "recorded_at": now
        }).execute()
        
        return {"recorded_at": now}
    
    def update_location_with_smoothing(
        self,
        driver_id: UUID,
        location: LocationUpdateDTO
    ) -> Tuple[bool, str, dict]:
        """
        Cập nhật vị trí với data smoothing
        - Luôn cập nhật current location (real-time)
        - Chỉ lưu history nếu đạt threshold
        
        Args:
            driver_id: UUID của driver
            location: DTO chứa thông tin vị trí
            
        Returns:
            Tuple (saved_to_history: bool, reason: str, broadcast_data: dict)
        """
        # 1. Luôn cập nhật vị trí hiện tại (cho real-time tracking)
        self.update_current_location(driver_id, location)
        
        # 2. Kiểm tra có nên lưu vào history không
        should_save, reason = self.smoother.should_save_point(
            driver_id=str(driver_id),
            lat=location.lat,
            lng=location.lng,
            timestamp=datetime.now(),
            speed=location.speed
        )
        
        # 3. Chỉ lưu history nếu đạt threshold
        if should_save:
            self.save_location_history(driver_id, location)
        
        # 4. Build broadcast data
        broadcast_data = self.build_broadcast_data(driver_id, location)
        broadcast_data["saved_to_history"] = should_save
        broadcast_data["save_reason"] = reason
        
        return should_save, reason, broadcast_data
    
    def build_broadcast_data(self, driver_id: UUID, location: LocationUpdateDTO) -> dict:
        """
        Tạo data để broadcast qua WebSocket
        
        Args:
            driver_id: UUID của driver
            location: DTO chứa thông tin vị trí
            
        Returns:
            Dict chứa thông tin để broadcast
        """
        return {
            "driver_id": str(driver_id),
            "lat": location.lat,
            "lng": location.lng,
            "speed": location.speed,
            "heading": location.heading,
            "status": location.status,
            "schedule_id": str(location.schedule_id) if location.schedule_id else None,
            "order_detail_id": str(location.order_detail_id) if location.order_detail_id else None,
            "timestamp": datetime.now().isoformat()
        }
    
    # ================== GET CURRENT LOCATION ==================
    
    def get_current_location(self, driver_id: UUID) -> Optional[dict]:
        """
        Lấy vị trí hiện tại của driver
        
        Args:
            driver_id: UUID của driver
            
        Returns:
            Dict chứa thông tin vị trí hoặc None nếu không tìm thấy
        """
        res = (
            self.supabase.schema("delivery")
            .table("driver_current_locations")
            .select("*, drivers(name, phone)")
            .eq("driver_id", str(driver_id))
            .single()
            .execute()
        )
        
        if not res.data:
            return None
        
        data = res.data
        loc = parse_point(data.get("location"))
        
        return {
            "driver_id": data["driver_id"],
            "driver_name": data.get("drivers", {}).get("name") if data.get("drivers") else None,
            "lat": loc["lat"] if loc else None,
            "lng": loc["lng"] if loc else None,
            "speed": data.get("speed"),
            "heading": data.get("heading"),
            "status": data.get("status"),
            "schedule_id": data.get("schedule_id"),
            "order_detail_id": data.get("current_order_detail_id"),
            "updated_at": data.get("updated_at")
        }
    
    # ================== GET HISTORY ==================
    
    def get_driver_history(
        self,
        driver_id: UUID,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        schedule_id: Optional[UUID] = None,
        limit: int = 1000
    ) -> List[dict]:
        """
        Lấy lịch sử di chuyển của driver
        
        Args:
            driver_id: UUID của driver
            start_time: Thời gian bắt đầu (optional)
            end_time: Thời gian kết thúc (optional)
            schedule_id: Lọc theo schedule (optional)
            limit: Số lượng record tối đa
            
        Returns:
            Danh sách các điểm trong lịch sử
        """
        query = (
            self.supabase.schema("delivery")
            .table("driver_location_history")
            .select("*")
            .eq("driver_id", str(driver_id))
            .order("recorded_at", desc=False)
            .limit(limit)
        )
        
        if schedule_id:
            query = query.eq("schedule_id", str(schedule_id))
        if start_time:
            query = query.gte("recorded_at", start_time.isoformat())
        if end_time:
            query = query.lte("recorded_at", end_time.isoformat())
        
        res = query.execute()
        
        return [self._parse_history_item(item) for item in res.data]
    
    def get_driver_history_compressed(
        self,
        driver_id: UUID,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        epsilon: float = 0.00005
    ) -> dict:
        """
        Lấy lịch sử di chuyển đã được nén bằng Douglas-Peucker
        
        Args:
            driver_id: UUID của driver
            start_time: Thời gian bắt đầu
            end_time: Thời gian kết thúc
            epsilon: Ngưỡng nén (càng nhỏ càng chi tiết)
            
        Returns:
            Dict chứa original_count, compressed_count, compression_ratio, points
        """
        # Lấy dữ liệu gốc
        original_points = self.get_driver_history(
            driver_id=driver_id,
            start_time=start_time,
            end_time=end_time,
            limit=10000  # Lấy nhiều để nén
        )
        
        if len(original_points) < 3:
            return {
                "original_count": len(original_points),
                "compressed_count": len(original_points),
                "compression_ratio": 1.0,
                "points": original_points
            }
        
        # Áp dụng Douglas-Peucker
        compressed_points = LocationSmoother.douglas_peucker(original_points, epsilon)
        
        return {
            "original_count": len(original_points),
            "compressed_count": len(compressed_points),
            "compression_ratio": round(len(compressed_points) / len(original_points), 3),
            "points": compressed_points
        }
    
    def get_schedule_route(self, schedule_id: UUID) -> List[dict]:
        """
        Lấy toàn bộ tuyến đường của 1 lịch giao hàng
        
        Args:
            schedule_id: UUID của schedule
            
        Returns:
            Danh sách các điểm trong tuyến đường
        """
        res = (
            self.supabase.schema("delivery")
            .table("driver_location_history")
            .select("*")
            .eq("schedule_id", str(schedule_id))
            .order("recorded_at", desc=False)
            .execute()
        )
        
        return [self._parse_history_item(item) for item in res.data]
    
    # ================== GET ACTIVE DRIVERS ==================
    
    def get_active_drivers(
        self,
        minutes: int = 5,
        post_office_id: Optional[UUID] = None
    ) -> List[dict]:
        """
        Lấy tất cả drivers đang hoạt động (có cập nhật trong X phút gần đây)
        
        Args:
            minutes: Số phút để coi là "đang hoạt động"
            post_office_id: Lọc theo bưu cục (optional)
            
        Returns:
            Danh sách drivers đang hoạt động
        """
        threshold = (datetime.now() - timedelta(minutes=minutes)).isoformat()
        
        res = (
            self.supabase.schema("delivery")
            .table("driver_current_locations")
            .select("*, drivers(id, name, phone, post_office_id)")
            .gte("updated_at", threshold)
            .execute()
        )
        
        result = []
        for item in res.data:
            driver = item.get("drivers", {})
            
            # Filter by post_office_id nếu có
            if post_office_id and driver.get("post_office_id") != str(post_office_id):
                continue
            
            loc = parse_point(item.get("location"))
            result.append({
                "driver_id": item["driver_id"],
                "driver_name": driver.get("name") if driver else None,
                "driver_phone": driver.get("phone") if driver else None,
                "post_office_id": driver.get("post_office_id") if driver else None,
                "lat": loc["lat"] if loc else None,
                "lng": loc["lng"] if loc else None,
                "speed": item.get("speed"),
                "heading": item.get("heading"),
                "status": item.get("status"),
                "schedule_id": item.get("schedule_id"),
                "updated_at": item.get("updated_at")
            })
        
        return result
    
    # ================== DRIVER STATUS ==================
    
    def set_driver_offline(self, driver_id: UUID) -> None:
        """
        Đánh dấu driver offline và clear cache
        
        Args:
            driver_id: UUID của driver
        """
        # Clear smoother cache
        self.smoother.clear_driver_cache(str(driver_id))
        
        # Update status trong database
        self.supabase.schema("delivery").table("driver_current_locations").update({
            "status": "offline",
            "updated_at": datetime.now().isoformat()
        }).eq("driver_id", str(driver_id)).execute()
    
    # ================== PRIVATE HELPERS ==================
    
    def _parse_history_item(self, item: dict) -> dict:
        """
        Parse 1 record từ history table
        
        Args:
            item: Raw record từ database
            
        Returns:
            Parsed dict với lat/lng riêng biệt
        """
        loc = parse_point(item.get("location"))
        return {
            "id": item["id"],
            "driver_id": item["driver_id"],
            "schedule_id": item.get("schedule_id"),
            "order_detail_id": item.get("order_detail_id"),
            "lat": loc["lat"] if loc else None,
            "lng": loc["lng"] if loc else None,
            "speed": item.get("speed"),
            "heading": item.get("heading"),
            "status": item.get("status"),
            "recorded_at": item.get("recorded_at")
        }

# Smoother instance riêng (nếu cần dùng độc lập)
location_smoother = LocationSmoother()