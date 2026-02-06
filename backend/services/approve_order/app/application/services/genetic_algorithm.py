# application/services/genetic_algorithm.py
"""
Genetic Algorithm cho việc gom đơn hàng thành schedules
CHỈ gom đơn theo area_code và cân bằng số đơn
KHÔNG tính khoảng cách (có API riêng để tối ưu route)
"""
import random
import math
import time
from typing import List, Dict, Tuple
from dataclasses import dataclass


@dataclass
class Individual:
    """
    Cá thể trong quần thể GA
    chromosome: [(schedule_idx, order_idx), ...] - mỗi đơn thuộc về schedule nào
    """
    chromosome: List[Tuple[int, int]]
    fitness: float = 0.0
    balance_score: float = 0.0
    priority_score: float = 0.0
    area_score: float = 0.0


class GeneticAlgorithmScheduler:
    """
    Thuật toán di truyền để gom đơn hàng thành các schedules
    
    Mục tiêu:
    - Gom đơn cùng khu vực (area_code)
    - Cân bằng số đơn giữa các schedules
    - Ưu tiên đơn có priority cao
    
    KHÔNG tính khoảng cách - có API riêng để tối ưu route
    """

    def __init__(
        self,
        orders: List[dict],
        max_orders_per_schedule: int = 15,
        max_distance_km: float = 40.0,  
        population_size: int = 50,
        generations: int = 100,
        mutation_rate: float = 0.1,
        crossover_rate: float = 0.8,
        elite_size: int = 5
    ):
        self.orders = orders
        self.num_orders = len(orders)
        self.max_orders_per_schedule = max_orders_per_schedule
        
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.elite_size = elite_size

        # Tính số schedule cần thiết (ước lượng)
        self.num_schedules = max(1, (self.num_orders + max_orders_per_schedule - 1) // max_orders_per_schedule)

    def _create_random_individual(self) -> Individual:
        """Tạo cá thể ngẫu nhiên"""
        chromosome = []
        orders_per_schedule = [0] * self.num_schedules

        order_indices = list(range(self.num_orders))
        random.shuffle(order_indices)

        for order_idx in order_indices:
            # Chọn schedule chưa đầy
            available = [
                i for i in range(self.num_schedules)
                if orders_per_schedule[i] < self.max_orders_per_schedule
            ]

            if not available:
                # Tạo thêm schedule mới
                self.num_schedules += 1
                orders_per_schedule.append(0)
                available = [self.num_schedules - 1]

            schedule_idx = random.choice(available)
            chromosome.append((schedule_idx, order_idx))
            orders_per_schedule[schedule_idx] += 1

        individual = Individual(chromosome=chromosome)
        self._calculate_fitness(individual)
        return individual

    def _create_greedy_individual(self) -> Individual:
        """Tạo cá thể theo heuristic - gom theo area_code"""
        chromosome = []
        orders_per_schedule = [0] * self.num_schedules

        # Nhóm theo area_code
        area_groups: Dict[str, List[int]] = {}
        for idx, order in enumerate(self.orders):
            area = order.get('area_code', 'unknown')
            if area not in area_groups:
                area_groups[area] = []
            area_groups[area].append(idx)

        # Sắp xếp mỗi nhóm theo priority
        for area in area_groups:
            area_groups[area].sort(
                key=lambda idx: self.orders[idx].get('priority_score', 0),
                reverse=True
            )

        schedule_idx = 0
        for area, order_indices in area_groups.items():
            for order_idx in order_indices:
                # Kiểm tra schedule hiện tại còn chỗ không
                while schedule_idx < len(orders_per_schedule) and \
                      orders_per_schedule[schedule_idx] >= self.max_orders_per_schedule:
                    schedule_idx += 1

                if schedule_idx >= len(orders_per_schedule):
                    # Tạo schedule mới
                    self.num_schedules += 1
                    orders_per_schedule.append(0)

                chromosome.append((schedule_idx, order_idx))
                orders_per_schedule[schedule_idx] += 1

        individual = Individual(chromosome=chromosome)
        self._calculate_fitness(individual)
        return individual

    def _calculate_fitness(self, individual: Individual) -> float:
        """
        Tính fitness - cao hơn = tốt hơn
        
        Tiêu chí:
        1. Cân bằng số đơn giữa schedules
        2. Gom đơn cùng area_code
        3. Ưu tiên đơn priority cao
        
        KHÔNG tính khoảng cách
        """
        if not individual.chromosome:
            individual.fitness = 0.0
            return 0.0

        # Nhóm đơn theo schedule
        schedule_orders: Dict[int, List[int]] = {}
        for schedule_idx, order_idx in individual.chromosome:
            if schedule_idx not in schedule_orders:
                schedule_orders[schedule_idx] = []
            schedule_orders[schedule_idx].append(order_idx)

        # 1. Tính độ cân bằng (số đơn giữa các schedules)
        orders_counts = [len(orders) for orders in schedule_orders.values()]
        if orders_counts:
            mean_orders = sum(orders_counts) / len(orders_counts)
            variance = sum((x - mean_orders) ** 2 for x in orders_counts) / len(orders_counts)
            balance_score = 1.0 / (1.0 + math.sqrt(variance))
        else:
            balance_score = 0.0

        # 2. Tính điểm gom area (đơn cùng area trong cùng schedule)
        area_score = 0.0
        for orders in schedule_orders.values():
            if len(orders) > 1:
                areas = [self.orders[idx].get('area_code') for idx in orders]
                # Đếm số cặp cùng area
                for i in range(len(areas)):
                    for j in range(i + 1, len(areas)):
                        if areas[i] == areas[j]:
                            area_score += 1

        # 3. Tính điểm priority
        total_priority = sum(
            self.orders[order_idx].get('priority_score', 0)
            for _, order_idx in individual.chromosome
        )

        # Công thức fitness (KHÔNG có distance)
        fitness = (
            len(individual.chromosome) * 5 +  # Bonus xếp được nhiều đơn
            total_priority * 2 +
            balance_score * 50 +
            area_score * 3
        )

        individual.fitness = fitness
        individual.balance_score = balance_score
        individual.priority_score = total_priority
        individual.area_score = area_score

        return fitness

    def _selection(self, population: List[Individual]) -> List[Individual]:
        """Tournament selection"""
        selected = []
        tournament_size = 5

        for _ in range(len(population)):
            tournament = random.sample(population, min(tournament_size, len(population)))
            winner = max(tournament, key=lambda ind: ind.fitness)
            selected.append(winner)

        return selected

    def _crossover(self, parent1: Individual, parent2: Individual) -> Tuple[Individual, Individual]:
        """Order crossover"""
        if random.random() > self.crossover_rate:
            return parent1, parent2

        # Lấy tất cả orders
        all_orders = set(order_idx for _, order_idx in parent1.chromosome)
        all_orders.update(order_idx for _, order_idx in parent2.chromosome)

        if len(all_orders) < 2:
            return parent1, parent2

        all_orders = list(all_orders)
        size = len(all_orders)
        point1 = random.randint(0, size - 1)
        point2 = random.randint(point1 + 1, size)

        # Tạo offspring
        mid_orders = set(all_orders[point1:point2])

        child1_chromosome = []
        child2_chromosome = []

        # Copy đoạn giữa
        for schedule_idx, order_idx in parent1.chromosome:
            if order_idx in mid_orders:
                child1_chromosome.append((schedule_idx, order_idx))

        for schedule_idx, order_idx in parent2.chromosome:
            if order_idx in mid_orders:
                child2_chromosome.append((schedule_idx, order_idx))

        # Điền phần còn lại
        for schedule_idx, order_idx in parent2.chromosome:
            if order_idx not in mid_orders:
                child1_chromosome.append((schedule_idx, order_idx))

        for schedule_idx, order_idx in parent1.chromosome:
            if order_idx not in mid_orders:
                child2_chromosome.append((schedule_idx, order_idx))

        child1 = Individual(chromosome=child1_chromosome)
        child2 = Individual(chromosome=child2_chromosome)

        self._calculate_fitness(child1)
        self._calculate_fitness(child2)

        return child1, child2

    def _mutate(self, individual: Individual) -> Individual:
        """Đột biến"""
        if random.random() > self.mutation_rate:
            return individual

        if len(individual.chromosome) < 2:
            return individual

        mutation_type = random.choice(['swap', 'move', 'merge'])

        if mutation_type == 'swap':
            # Hoán đổi 2 đơn giữa 2 schedules
            idx1, idx2 = random.sample(range(len(individual.chromosome)), 2)
            s1, o1 = individual.chromosome[idx1]
            s2, o2 = individual.chromosome[idx2]
            individual.chromosome[idx1] = (s2, o1)
            individual.chromosome[idx2] = (s1, o2)

        elif mutation_type == 'move':
            # Di chuyển đơn sang schedule khác
            idx = random.randint(0, len(individual.chromosome) - 1)
            _, order_idx = individual.chromosome[idx]
            new_schedule = random.randint(0, self.num_schedules - 1)
            individual.chromosome[idx] = (new_schedule, order_idx)

        elif mutation_type == 'merge':
            # Gộp 2 schedules nếu tổng đơn <= max
            schedule_orders: Dict[int, int] = {}
            for s, _ in individual.chromosome:
                schedule_orders[s] = schedule_orders.get(s, 0) + 1

            schedules = list(schedule_orders.keys())
            if len(schedules) >= 2:
                s1, s2 = random.sample(schedules, 2)
                if schedule_orders[s1] + schedule_orders[s2] <= self.max_orders_per_schedule:
                    # Merge s2 vào s1
                    individual.chromosome = [
                        (s1 if s == s2 else s, o) 
                        for s, o in individual.chromosome
                    ]

        self._calculate_fitness(individual)
        return individual

    def optimize(self) -> Tuple[Individual, List[Dict]]:
        """Chạy thuật toán GA"""
        start_time = time.time()

        # Khởi tạo quần thể
        population = []
        
        # 20% greedy
        num_greedy = max(1, self.population_size // 5)
        for _ in range(num_greedy):
            population.append(self._create_greedy_individual())

        # 80% random
        while len(population) < self.population_size:
            population.append(self._create_random_individual())

        stats = []
        best_individual = max(population, key=lambda ind: ind.fitness)

        for generation in range(self.generations):
            # Selection
            selected = self._selection(population)

            # Tạo thế hệ mới
            next_population = []

            # Giữ elite
            sorted_pop = sorted(population, key=lambda ind: ind.fitness, reverse=True)
            next_population.extend(sorted_pop[:self.elite_size])

            # Crossover và Mutation
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

            # Early stopping
            if generation > 20:
                recent = [s['best_fitness'] for s in stats[-20:]]
                if max(recent) - min(recent) < 0.1:
                    break

        execution_time = time.time() - start_time
        stats.append({'execution_time_seconds': execution_time})

        return best_individual, stats