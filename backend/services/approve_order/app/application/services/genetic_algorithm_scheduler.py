import random
import math
import time
from typing import List, Dict, Tuple, Optional
from uuid import UUID, uuid4
from datetime import date
from dataclasses import dataclass
import numpy as np


@dataclass
class Individual:
    """Cá thể trong quần thể GA - đại diện cho 1 phương án xếp lịch"""
    chromosome: List[Tuple[int, int]]  # [(driver_idx, order_idx), ...]
    fitness: float = 0.0
    total_distance: float = 0.0
    balance_score: float = 0.0
    priority_score: float = 0.0


class GeneticAlgorithmScheduler:
    """Thuật toán di truyền để xếp lịch tài xế"""

    def __init__(
            self,
            drivers: List[dict],
            orders: List[dict],
            shift_config: dict,
            population_size: int = 50,
            generations: int = 100,
            mutation_rate: float = 0.1,
            crossover_rate: float = 0.8,
            elite_size: int = 5
    ):
        self.drivers = drivers
        self.orders = orders
        self.shift_config = shift_config
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.elite_size = elite_size

        self.num_drivers = len(drivers)
        self.num_orders = len(orders)
        self.max_orders_per_driver = shift_config.get('max_orders_per_driver', 20)
        self.max_distance_km = shift_config.get('max_distance_km', 50.0)

        # Cache khoảng cách giữa các điểm
        self.distance_cache: Dict[Tuple[int, int], float] = {}
        self._precompute_distances()

    def _precompute_distances(self):
        """Tính trước khoảng cách giữa các điểm"""
        for i in range(self.num_orders):
            for j in range(self.num_orders):
                if i != j:
                    key = (i, j)
                    self.distance_cache[key] = self._calculate_distance(
                        self.orders[i]['location'],
                        self.orders[j]['location']
                    )

    @staticmethod
    def _calculate_distance(point1: tuple, point2: tuple) -> float:
        """Tính khoảng cách Haversine giữa 2 điểm (lat, lon)"""
        if not point1 or not point2:
            return 0.0

        lat1, lon1 = point1
        lat2, lon2 = point2

        # Radius of Earth in kilometers
        R = 6371.0

        # Convert to radians
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)

        # Haversine formula
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad

        a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        distance = R * c
        return distance

    def _get_cached_distance(self, order_idx1: int, order_idx2: int) -> float:
        """Lấy khoảng cách từ cache"""
        return self.distance_cache.get((order_idx1, order_idx2), 0.0)

    def _create_random_individual(self) -> Individual:
        """Tạo cá thể ngẫu nhiên"""
        # Shuffle orders
        order_indices = list(range(self.num_orders))
        random.shuffle(order_indices)

        chromosome = []
        orders_per_driver = [0] * self.num_drivers

        for order_idx in order_indices:
            # Chọn tài xế ngẫu nhiên chưa đầy
            available_drivers = [
                i for i in range(self.num_drivers)
                if orders_per_driver[i] < self.max_orders_per_driver
            ]

            if not available_drivers:
                break

            driver_idx = random.choice(available_drivers)
            chromosome.append((driver_idx, order_idx))
            orders_per_driver[driver_idx] += 1

        individual = Individual(chromosome=chromosome)
        self._calculate_fitness(individual)
        return individual

    def _create_greedy_individual(self) -> Individual:
        """Tạo cá thể theo heuristic tham lam (ưu tiên priority và khoảng cách)"""
        chromosome = []
        orders_per_driver = [0] * self.num_drivers
        assigned_orders = set()

        # Sort orders by priority descending
        sorted_orders = sorted(
            enumerate(self.orders),
            key=lambda x: (-x[1]['priority_score'], x[0])
        )

        for order_idx, order in sorted_orders:
            if order_idx in assigned_orders:
                continue

            # Tìm tài xế phù hợp nhất
            best_driver_idx = None
            best_score = float('inf')

            for driver_idx in range(self.num_drivers):
                if orders_per_driver[driver_idx] >= self.max_orders_per_driver:
                    continue

                # Tính score dựa trên vị trí hiện tại của tài xế
                driver_location = self.drivers[driver_idx].get('location')
                if driver_location:
                    distance = self._calculate_distance(
                        driver_location,
                        order['location']
                    )

                    # Score thấp hơn = tốt hơn
                    score = distance - order['priority_score'] * 0.5

                    if score < best_score:
                        best_score = score
                        best_driver_idx = driver_idx

            if best_driver_idx is None:
                # Nếu không tìm được, chọn tài xế có ít đơn nhất
                best_driver_idx = min(
                    range(self.num_drivers),
                    key=lambda i: orders_per_driver[i]
                )

            if orders_per_driver[best_driver_idx] < self.max_orders_per_driver:
                chromosome.append((best_driver_idx, order_idx))
                orders_per_driver[best_driver_idx] += 1
                assigned_orders.add(order_idx)

        individual = Individual(chromosome=chromosome)
        self._calculate_fitness(individual)
        return individual

    def _calculate_fitness(self, individual: Individual) -> float:
        """
        Tính fitness cho cá thể
        Fitness cao hơn = tốt hơn
        """
        if not individual.chromosome:
            individual.fitness = 0.0
            return 0.0

        # Nhóm đơn hàng theo tài xế
        driver_orders: Dict[int, List[int]] = {i: [] for i in range(self.num_drivers)}
        for driver_idx, order_idx in individual.chromosome:
            driver_orders[driver_idx].append(order_idx)

        # 1. Tính tổng khoảng cách (càng thấp càng tốt)
        total_distance = 0.0
        for driver_idx, order_indices in driver_orders.items():
            if len(order_indices) <= 1:
                continue

            # Tính khoảng cách tuyến đường tối ưu (TSP đơn giản - nearest neighbor)
            route_distance = self._calculate_route_distance(order_indices)
            total_distance += route_distance

        # 2. Tính độ cân bằng công việc (std của số đơn hàng mỗi tài xế)
        orders_count = [len(orders) for orders in driver_orders.values()]
        if orders_count:
            mean_orders = sum(orders_count) / len(orders_count)
            variance = sum((x - mean_orders) ** 2 for x in orders_count) / len(orders_count)
            std_dev = math.sqrt(variance)
            balance_score = 1.0 / (1.0 + std_dev)  # Càng cân bằng càng cao
        else:
            balance_score = 0.0

        # 3. Tính điểm ưu tiên (tổng priority_score của các đơn được xếp)
        total_priority = sum(
            self.orders[order_idx]['priority_score']
            for _, order_idx in individual.chromosome
        )
        priority_score = total_priority

        # 4. Penalty cho việc vượt quá khoảng cách tối đa
        distance_penalty = 0.0
        for driver_idx, order_indices in driver_orders.items():
            if order_indices:
                route_distance = self._calculate_route_distance(order_indices)
                if route_distance > self.max_distance_km:
                    distance_penalty += (route_distance - self.max_distance_km) * 10

        # 5. Bonus cho việc xếp được nhiều đơn
        coverage_bonus = len(individual.chromosome) * 5

        # Công thức fitness (tối đa hóa)
        fitness = (
                coverage_bonus +
                priority_score * 2 +
                balance_score * 50 -
                total_distance * 2 -
                distance_penalty
        )

        individual.fitness = fitness
        individual.total_distance = total_distance
        individual.balance_score = balance_score
        individual.priority_score = priority_score

        return fitness

    def _calculate_route_distance(self, order_indices: List[int]) -> float:
        """Tính khoảng cách tuyến đường cho danh sách đơn hàng"""
        if len(order_indices) <= 1:
            return 0.0

        # Simple nearest neighbor
        total_distance = 0.0
        for i in range(len(order_indices) - 1):
            distance = self._get_cached_distance(
                order_indices[i],
                order_indices[i + 1]
            )
            total_distance += distance

        return total_distance

    def _initialize_population(self) -> List[Individual]:
        """Khởi tạo quần thể ban đầu"""
        population = []

        # Thêm 20% cá thể greedy
        num_greedy = max(1, self.population_size // 5)
        for _ in range(num_greedy):
            population.append(self._create_greedy_individual())

        # Thêm 80% cá thể random
        while len(population) < self.population_size:
            population.append(self._create_random_individual())

        return population

    def _selection(self, population: List[Individual]) -> List[Individual]:
        """Chọn lọc: Tournament selection"""
        selected = []
        tournament_size = 5

        for _ in range(len(population)):
            tournament = random.sample(population, min(tournament_size, len(population)))
            winner = max(tournament, key=lambda ind: ind.fitness)
            selected.append(winner)

        return selected

    def _crossover(self, parent1: Individual, parent2: Individual) -> Tuple[Individual, Individual]:
        """Lai ghép: Order crossover (OX)"""
        if random.random() > self.crossover_rate:
            return parent1, parent2

        # Lấy tất cả các order_idx từ cả 2 parent
        all_orders = set()
        for _, order_idx in parent1.chromosome:
            all_orders.add(order_idx)
        for _, order_idx in parent2.chromosome:
            all_orders.add(order_idx)

        all_orders = list(all_orders)

        if len(all_orders) < 2:
            return parent1, parent2

        # Chọn 2 điểm cắt
        size = len(all_orders)
        point1 = random.randint(0, size - 1)
        point2 = random.randint(point1 + 1, size)

        # Tạo offspring
        offspring1_orders = set(all_orders[point1:point2])
        offspring2_orders = set(all_orders[point1:point2])

        # Copy driver assignment từ parent vào đoạn giữa
        offspring1_chromosome = []
        offspring2_chromosome = []

        # Lấy driver assignment cho đoạn giữa từ parent1
        for driver_idx, order_idx in parent1.chromosome:
            if order_idx in offspring1_orders:
                offspring1_chromosome.append((driver_idx, order_idx))

        # Lấy driver assignment cho đoạn giữa từ parent2
        for driver_idx, order_idx in parent2.chromosome:
            if order_idx in offspring2_orders:
                offspring2_chromosome.append((driver_idx, order_idx))

        # Điền các order còn lại từ parent2 vào offspring1
        for driver_idx, order_idx in parent2.chromosome:
            if order_idx not in offspring1_orders:
                offspring1_chromosome.append((driver_idx, order_idx))

        # Điền các order còn lại từ parent1 vào offspring2
        for driver_idx, order_idx in parent1.chromosome:
            if order_idx not in offspring2_orders:
                offspring2_chromosome.append((driver_idx, order_idx))

        child1 = Individual(chromosome=offspring1_chromosome)
        child2 = Individual(chromosome=offspring2_chromosome)

        self._calculate_fitness(child1)
        self._calculate_fitness(child2)

        return child1, child2

    def _mutate(self, individual: Individual) -> Individual:
        """Đột biến"""
        if random.random() > self.mutation_rate:
            return individual

        if len(individual.chromosome) < 2:
            return individual

        mutation_type = random.choice(['swap', 'reassign', 'reverse'])

        if mutation_type == 'swap':
            # Hoán đổi 2 đơn hàng
            idx1, idx2 = random.sample(range(len(individual.chromosome)), 2)
            individual.chromosome[idx1], individual.chromosome[idx2] = \
                individual.chromosome[idx2], individual.chromosome[idx1]

        elif mutation_type == 'reassign':
            # Gán lại đơn hàng cho tài xế khác
            idx = random.randint(0, len(individual.chromosome) - 1)
            driver_idx, order_idx = individual.chromosome[idx]
            new_driver_idx = random.randint(0, self.num_drivers - 1)
            individual.chromosome[idx] = (new_driver_idx, order_idx)

        elif mutation_type == 'reverse':
            # Đảo ngược một đoạn
            if len(individual.chromosome) >= 2:
                idx1 = random.randint(0, len(individual.chromosome) - 2)
                idx2 = random.randint(idx1 + 1, len(individual.chromosome))
                individual.chromosome[idx1:idx2] = reversed(individual.chromosome[idx1:idx2])

        self._calculate_fitness(individual)
        return individual

    def optimize(self) -> Tuple[Individual, List[Dict]]:
        """Chạy thuật toán GA"""
        start_time = time.time()

        # Khởi tạo quần thể
        population = self._initialize_population()

        stats = []
        best_individual = max(population, key=lambda ind: ind.fitness)

        for generation in range(self.generations):
            # Selection
            selected = self._selection(population)

            # Crossover and Mutation
            next_population = []

            # Giữ lại elite
            sorted_population = sorted(population, key=lambda ind: ind.fitness, reverse=True)
            next_population.extend(sorted_population[:self.elite_size])

            # Tạo thế hệ mới
            while len(next_population) < self.population_size:
                parent1, parent2 = random.sample(selected, 2)
                child1, child2 = self._crossover(parent1, parent2)
                child1 = self._mutate(child1)
                child2 = self._mutate(child2)

                next_population.append(child1)
                if len(next_population) < self.population_size:
                    next_population.append(child2)

            population = next_population

            # Thống kê
            current_best = max(population, key=lambda ind: ind.fitness)
            if current_best.fitness > best_individual.fitness:
                best_individual = current_best

            fitnesses = [ind.fitness for ind in population]
            stats.append({
                'generation': generation,
                'best_fitness': max(fitnesses),
                'average_fitness': sum(fitnesses) / len(fitnesses),
                'worst_fitness': min(fitnesses)
            })

            # Early stopping nếu không cải thiện trong 20 thế hệ
            if generation > 20:
                recent_best = [s['best_fitness'] for s in stats[-20:]]
                if max(recent_best) - min(recent_best) < 0.1:
                    print(f"Early stopping at generation {generation}")
                    break

        execution_time = time.time() - start_time
        stats.append({'execution_time_seconds': execution_time})

        return best_individual, stats