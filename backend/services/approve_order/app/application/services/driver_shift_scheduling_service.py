from typing import List, Dict, Tuple
from uuid import UUID, uuid4
from datetime import date
import asyncio

from application.services.genetic_algorithm_scheduler import GeneticAlgorithmScheduler, Individual
from infrastructure.repositories.driver_scheduling_repository import DriverSchedulingRepository
from application.dto.driver_shift_dto import (
    SchedulingRequest,
    SchedulingResponse,
    ScheduleAssignment,
    DriverAvailability,
    OrderDetailForScheduling
)




class DriverShiftSchedulingService:
    """Service xếp lịch ca làm việc cho tài xế"""

    def __init__(self, supabase_client):
        self.repository = DriverSchedulingRepository(supabase_client)

    async def schedule_shifts(
            self,
            request: SchedulingRequest
    ) -> SchedulingResponse:
        """
        Xếp lịch ca làm việc cho tài xế sử dụng thuật toán GA

        Args:
            request: Thông tin request xếp lịch

        Returns:
            SchedulingResponse: Kết quả xếp lịch
        """
        # 1. Lấy danh sách tài xế available
        drivers_data = await self.repository.get_available_drivers(
            post_office_id=request.post_office_id,
            scheduled_date=request.scheduled_date
        )

        if not drivers_data:
            raise ValueError("Không có tài xế available cho ngày này")

        # 2. Lấy danh sách đơn hàng cần xếp lịch
        orders_data = await self.repository.get_pending_orders_by_area(
            area_codes=request.area_codes,
            post_office_id=request.post_office_id
        )

        if not orders_data:
            raise ValueError("Không có đơn hàng nào cần xếp lịch")

        # 3. Chạy thuật toán GA cho từng ca (chạy synchronous vì GA không async)
        all_assignments = []
        all_unassigned = set(range(len(orders_data)))
        best_fitness = 0.0
        algorithm_stats = []

        for shift_config in request.shift_configs:
            # Prepare data cho GA
            shift_config_dict = {
                'max_orders_per_driver': shift_config.max_orders_per_driver,
                'max_distance_km': shift_config.max_distance_km
            }

            # Chạy GA trong executor để không block event loop
            loop = asyncio.get_event_loop()
            best_solution, stats = await loop.run_in_executor(
                None,
                self._run_ga_optimization,
                drivers_data,
                orders_data,
                shift_config_dict,
                request
            )

            best_fitness += best_solution.fitness
            algorithm_stats.extend(stats)

            # Chuyển đổi solution thành assignments
            assignments = self._convert_solution_to_assignments(
                solution=best_solution,
                drivers=drivers_data,
                orders=orders_data,
                shift_name=shift_config.shift_name
            )

            all_assignments.extend(assignments)

            # Cập nhật danh sách đơn chưa được xếp
            assigned_orders = set()
            for _, order_idx in best_solution.chromosome:
                assigned_orders.add(order_idx)
            all_unassigned -= assigned_orders

        # 4. Lưu vào database
        schedule_id = await self._save_schedules(
            assignments=all_assignments,
            scheduled_date=request.scheduled_date,
            orders_data=orders_data,
            post_office_id=request.post_office_id
        )

        # 5. Trả về kết quả
        unassigned_order_ids = [
            UUID(orders_data[idx]['id'])
            for idx in all_unassigned
        ]

        return SchedulingResponse(
            schedule_id=schedule_id,
            scheduled_date=request.scheduled_date,
            post_office_id=request.post_office_id,
            assignments=all_assignments,
            total_orders_scheduled=len(orders_data) - len(all_unassigned),
            unassigned_orders=unassigned_order_ids,
            fitness_score=best_fitness,
            algorithm_info={
                'population_size': request.population_size,
                'generations': request.generations,
                'mutation_rate': request.mutation_rate,
                'crossover_rate': request.crossover_rate,
                'stats': algorithm_stats
            }
        )

    def _run_ga_optimization(
            self,
            drivers_data: List[dict],
            orders_data: List[dict],
            shift_config_dict: dict,
            request: SchedulingRequest
    ) -> Tuple[Individual, List[Dict]]:
        """Chạy GA optimization (synchronous)"""
        ga = GeneticAlgorithmScheduler(
            drivers=drivers_data,
            orders=orders_data,
            shift_config=shift_config_dict,
            population_size=request.population_size,
            generations=request.generations,
            mutation_rate=request.mutation_rate,
            crossover_rate=request.crossover_rate,
            elite_size=request.elite_size
        )

        return ga.optimize()

    def _convert_solution_to_assignments(
            self,
            solution: Individual,
            drivers: List[dict],
            orders: List[dict],
            shift_name: str
    ) -> List[ScheduleAssignment]:
        """Chuyển đổi solution GA thành danh sách assignments"""
        # Nhóm đơn hàng theo tài xế
        driver_orders: Dict[int, List[int]] = {}
        for driver_idx, order_idx in solution.chromosome:
            if driver_idx not in driver_orders:
                driver_orders[driver_idx] = []
            driver_orders[driver_idx].append(order_idx)

        assignments = []

        for driver_idx, order_indices in driver_orders.items():
            if not order_indices:
                continue

            driver = drivers[driver_idx]

            # Tối ưu hóa route (TSP - nearest neighbor)
            optimized_route = self._optimize_route(order_indices, orders)

            # Tính toán metrics
            total_distance = self._calculate_total_distance(optimized_route, orders)
            estimated_time = self._estimate_time(total_distance, len(optimized_route))

            assignment = ScheduleAssignment(
                driver_id=UUID(driver['id']),
                driver_name=driver['name'],
                shift_name=shift_name,
                order_detail_ids=[UUID(orders[idx]['id']) for idx in optimized_route],
                total_orders=len(optimized_route),
                estimated_distance_km=total_distance,
                estimated_time_hours=estimated_time,
                route_sequence=list(range(1, len(optimized_route) + 1))
            )

            assignments.append(assignment)

        return assignments

    def _optimize_route(
            self,
            order_indices: List[int],
            orders: List[dict]
    ) -> List[int]:
        """Tối ưu hóa route bằng nearest neighbor"""
        if len(order_indices) <= 1:
            return order_indices

        # Sort by priority first
        sorted_indices = sorted(
            order_indices,
            key=lambda idx: orders[idx]['priority_score'],
            reverse=True
        )

        # Simple nearest neighbor
        route = [sorted_indices[0]]
        remaining = set(sorted_indices[1:])

        while remaining:
            current_idx = route[-1]
            current_location = orders[current_idx]['location']

            if not current_location:
                # Nếu không có location, lấy order tiếp theo
                next_idx = remaining.pop()
                route.append(next_idx)
                continue

            # Tìm đơn hàng gần nhất
            nearest_idx = None
            min_distance = float('inf')

            for idx in remaining:
                order_location = orders[idx]['location']
                if order_location:
                    distance = self._haversine_distance(current_location, order_location)
                    if distance < min_distance:
                        min_distance = distance
                        nearest_idx = idx

            if nearest_idx is not None:
                route.append(nearest_idx)
                remaining.remove(nearest_idx)
            else:
                # Nếu không tìm được, lấy bất kỳ
                next_idx = remaining.pop()
                route.append(next_idx)

        return route

    @staticmethod
    def _haversine_distance(point1: tuple, point2: tuple) -> float:
        """Tính khoảng cách Haversine"""
        import math

        if not point1 or not point2:
            return 0.0

        lat1, lon1 = point1
        lat2, lon2 = point2

        R = 6371.0
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)

        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad

        a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c

    def _calculate_total_distance(
            self,
            route: List[int],
            orders: List[dict]
    ) -> float:
        """Tính tổng khoảng cách của route"""
        if len(route) <= 1:
            return 0.0

        total_distance = 0.0
        for i in range(len(route) - 1):
            loc1 = orders[route[i]]['location']
            loc2 = orders[route[i + 1]]['location']

            if loc1 and loc2:
                distance = self._haversine_distance(loc1, loc2)
                total_distance += distance

        return round(total_distance, 2)

    @staticmethod
    def _estimate_time(distance_km: float, num_orders: int) -> float:
        """Ước tính thời gian giao hàng"""
        # Giả sử: 30 km/h trung bình + 15 phút mỗi đơn
        travel_time = distance_km / 30.0
        delivery_time = num_orders * 0.25  # 15 phút = 0.25 giờ

        return round(travel_time + delivery_time, 2)

    async def _save_schedules(
            self,
            assignments: List[ScheduleAssignment],
            scheduled_date: date,
            orders_data: List[dict],
            post_office_id: UUID
    ) -> UUID:
        """Lưu schedules vào database"""
        # Tạo một schedule_id chung cho toàn bộ batch
        main_schedule_id = uuid4()

        for assignment in assignments:
            # Lấy area_code từ đơn hàng đầu tiên
            first_order_id = assignment.order_detail_ids[0]
            area_code = None
            for order in orders_data:
                if UUID(order['id']) == first_order_id:
                    area_code = order['area_code']
                    break

            # Tạo schedule cho tài xế
            schedule_id = await self.repository.create_schedule(
                driver_id=assignment.driver_id,
                scheduled_date=scheduled_date,
                area_code=area_code or '',
                post_office_id=post_office_id
            )

            # Tạo schedule items
            await self.repository.create_schedule_items(
                schedule_id=schedule_id,
                order_detail_ids=assignment.order_detail_ids,
                route_sequence=assignment.route_sequence
            )

            # Cập nhật trạng thái schedule
            await self.repository.update_schedule_status(
                schedule_id=schedule_id,
                status='confirmed'
            )

            # Cập nhật trạng thái tài xế
            await self.repository.update_driver_status(
                driver_id=assignment.driver_id,
                status='busy'
            )

        return main_schedule_id

    async def get_driver_schedule(
            self,
            driver_id: UUID,
            scheduled_date: date
    ) -> dict:
        """Lấy lịch làm việc của tài xế"""
        # TODO: Implement query để lấy schedule của tài xế
        pass

    async def update_schedule_status(
            self,
            schedule_id: UUID,
            status: str
    ) -> None:
        """Cập nhật trạng thái schedule"""
        await self.repository.update_schedule_status(schedule_id, status)