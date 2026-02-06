# application/services/ga_scheduling_service.py
"""
Service xếp lịch sử dụng Genetic Algorithm
"""
from typing import List, Dict, Tuple
from uuid import UUID, uuid4
from datetime import date
import asyncio

from application.services.genetic_algorithm import GeneticAlgorithmScheduler, Individual
from application.dto.scheduling_dto import (
    SchedulingRequest,
    SchedulingResponse,
    ScheduleResponse,
    ScheduleItemResponse,
    GAConfig
)
from infrastructure.repositories.ga_scheduling_repository import GASchedulingRepository


class GASchedulingService:
    """Service xếp lịch giao hàng sử dụng GA"""

    def __init__(self, supabase_client):
        self.repository = GASchedulingRepository(supabase_client)

    async def create_schedules(self, request: SchedulingRequest) -> SchedulingResponse:
        """
        Tạo schedules bằng Genetic Algorithm
        
        Flow:
        1. Lấy đơn hàng pending theo area_codes
        2. Chạy GA để tối ưu (gom đơn, tối ưu route)
        3. Tạo schedules (KHÔNG gán driver)
        4. Trả về kết quả
        """
        
        # 1. Lấy đơn hàng cần xếp lịch
        orders_data = await self.repository.get_pending_orders(
            area_codes=request.area_codes,
            post_office_id=request.post_office_id
        )

        if not orders_data:
            return SchedulingResponse(
                success=False,
                message="Không có đơn hàng nào cần xếp lịch",
                total_orders_processed=0,
                total_schedules_created=0
            )

        # 2. Chuẩn bị config cho GA
        ga_config = GAConfig(
            max_orders_per_schedule=request.max_orders_per_schedule,
            max_distance_km=request.max_distance_km,
            population_size=request.population_size,
            generations=request.generations,
            mutation_rate=request.mutation_rate,
            crossover_rate=request.crossover_rate,
            elite_size=request.elite_size
        )

        # 3. Chạy GA trong executor (không block event loop)
        loop = asyncio.get_event_loop()
        best_solution, stats = await loop.run_in_executor(
            None,
            self._run_ga_optimization,
            orders_data,
            ga_config
        )

        # 4. Chuyển solution thành schedules
        schedule_groups = self._convert_solution_to_groups(
            solution=best_solution,
            orders=orders_data,
            max_orders=request.max_orders_per_schedule
        )

        # 5. Lưu vào database
        created_schedules = await self._save_schedules(
            schedule_groups=schedule_groups,
            scheduled_date=request.scheduled_date,
            orders_data=orders_data,
            post_office_id=request.post_office_id
        )

        # 6. Tính đơn chưa được xếp
        assigned_order_ids = set()
        for group in schedule_groups:
            assigned_order_ids.update(group['order_indices'])
        
        unassigned = [
            orders_data[i]['id'] 
            for i in range(len(orders_data)) 
            if i not in assigned_order_ids
        ]

        return SchedulingResponse(
            success=True,
            message=f"Đã tạo {len(created_schedules)} schedules với {len(orders_data) - len(unassigned)} đơn hàng",
            total_orders_processed=len(orders_data) - len(unassigned),
            total_schedules_created=len(created_schedules),
            best_fitness_score=best_solution.fitness,
            generations_run=len(stats) - 1,  # -1 vì có execution_time ở cuối
            schedules=created_schedules,
            unassigned_order_ids=unassigned,
            warnings=[]
        )

    def _run_ga_optimization(
        self,
        orders_data: List[dict],
        ga_config: GAConfig
    ) -> Tuple[Individual, List[Dict]]:
        """Chạy GA optimization (synchronous)"""
        
        ga = GeneticAlgorithmScheduler(
            orders=orders_data,
            max_orders_per_schedule=ga_config.max_orders_per_schedule,
            max_distance_km=ga_config.max_distance_km,
            population_size=ga_config.population_size,
            generations=ga_config.generations,
            mutation_rate=ga_config.mutation_rate,
            crossover_rate=ga_config.crossover_rate,
            elite_size=ga_config.elite_size
        )

        return ga.optimize()

    def _convert_solution_to_groups(
        self,
        solution: Individual,
        orders: List[dict],
        max_orders: int
    ) -> List[Dict]:
        """
        Chuyển solution GA thành các nhóm schedule
        Mỗi nhóm = 1 schedule (chưa có driver)
        """
        # Nhóm đơn hàng theo schedule_idx từ chromosome
        schedule_orders: Dict[int, List[int]] = {}
        
        for schedule_idx, order_idx in solution.chromosome:
            if schedule_idx not in schedule_orders:
                schedule_orders[schedule_idx] = []
            schedule_orders[schedule_idx].append(order_idx)

        groups = []
        for schedule_idx, order_indices in schedule_orders.items():
            if not order_indices:
                continue

            # Tối ưu route trong nhóm
            optimized_route = self._optimize_route(order_indices, orders)
            
            # Tính metrics
            total_distance = self._calculate_total_distance(optimized_route, orders)
            
            # Lấy area_code từ đơn đầu tiên
            area_code = orders[optimized_route[0]]['area_code'] if optimized_route else ''

            groups.append({
                'order_indices': optimized_route,
                'area_code': area_code,
                'total_orders': len(optimized_route),
                'total_distance_km': total_distance
            })

        return groups

    def _optimize_route(self, order_indices: List[int], orders: List[dict]) -> List[int]:
        """Tối ưu route bằng nearest neighbor"""
        if len(order_indices) <= 1:
            return order_indices

        # Sort by priority first
        sorted_indices = sorted(
            order_indices,
            key=lambda idx: orders[idx].get('priority_score', 0),
            reverse=True
        )

        route = [sorted_indices[0]]
        remaining = set(sorted_indices[1:])

        while remaining:
            current_idx = route[-1]
            current_location = orders[current_idx].get('location')

            if not current_location:
                next_idx = remaining.pop()
                route.append(next_idx)
                continue

            # Tìm đơn gần nhất
            nearest_idx = None
            min_distance = float('inf')

            for idx in remaining:
                order_location = orders[idx].get('location')
                if order_location:
                    distance = self._haversine_distance(current_location, order_location)
                    if distance < min_distance:
                        min_distance = distance
                        nearest_idx = idx

            if nearest_idx is not None:
                route.append(nearest_idx)
                remaining.remove(nearest_idx)
            else:
                next_idx = remaining.pop()
                route.append(next_idx)

        return route

    @staticmethod
    def _haversine_distance(point1, point2) -> float:
        """Tính khoảng cách Haversine (km)"""
        import math

        if not point1 or not point2:
            return 0.0

        # Handle both tuple and dict format
        if isinstance(point1, dict):
            lat1, lon1 = point1.get('lat', 0), point1.get('lon', 0)
        else:
            lat1, lon1 = point1
            
        if isinstance(point2, dict):
            lat2, lon2 = point2.get('lat', 0), point2.get('lon', 0)
        else:
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

    def _calculate_total_distance(self, route: List[int], orders: List[dict]) -> float:
        """Tính tổng khoảng cách của route"""
        if len(route) <= 1:
            return 0.0

        total_distance = 0.0
        for i in range(len(route) - 1):
            loc1 = orders[route[i]].get('location')
            loc2 = orders[route[i + 1]].get('location')

            if loc1 and loc2:
                total_distance += self._haversine_distance(loc1, loc2)

        return round(total_distance, 2)

    async def _save_schedules(
        self,
        schedule_groups: List[Dict],
        scheduled_date: date,
        orders_data: List[dict],
        post_office_id: UUID
    ) -> List[ScheduleResponse]:
        """Lưu schedules vào database"""
        
        created_schedules = []

        for group in schedule_groups:
            order_indices = group['order_indices']
            if not order_indices:
                continue

            # Tạo schedule (KHÔNG có driver_id)
            schedule_id = await self.repository.create_schedule(
                scheduled_date=scheduled_date,
                area_code=group['area_code'],
                post_office_id=post_office_id,
                total_orders=group['total_orders']
            )

            # Tạo schedule items
            order_detail_ids = [orders_data[idx]['id'] for idx in order_indices]
            await self.repository.create_schedule_items(
                schedule_id=schedule_id,
                order_detail_ids=order_detail_ids
            )

            # Cập nhật status order_details
            await self.repository.update_order_details_status(
                order_detail_ids=order_detail_ids,
                status='scheduled'
            )

            # Build response
            items = [
                ScheduleItemResponse(
                    id="",  # Will be filled by DB
                    order_detail_id=orders_data[idx]['id'],
                    sequence_number=seq + 1,
                    address=orders_data[idx].get('address_detail'),
                    area_code=orders_data[idx].get('area_code'),
                    priority_score=orders_data[idx].get('priority_score')
                )
                for seq, idx in enumerate(order_indices)
            ]

            created_schedules.append(ScheduleResponse(
                id=str(schedule_id),
                area_code=group['area_code'],
                scheduled_date=scheduled_date,
                status='draft',
                total_orders=group['total_orders'],
                total_distance_km=group['total_distance_km'],
                items=items,
                driver_id=None,
                driver_name=None
            ))

        return created_schedules
