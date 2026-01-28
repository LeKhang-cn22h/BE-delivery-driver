"""
Genetic Algorithm for Driver Scheduling Optimization
"""
import random
import numpy as np
from typing import List, Tuple, Dict
from dataclasses import dataclass
from uuid import UUID

from domain.entities.driver import Driver
from domain.entities.order import OrderDetail
from infrastructure.config.settings import get_settings


@dataclass
class Gene:
    """Represents an order-driver assignment"""
    order_id: UUID
    driver_id: UUID
    queue_position: int  # Vị trí trong danh sách giao hàng của tài xế


@dataclass
class Chromosome:
    """Represents a complete scheduling solution"""
    genes: List[Gene]
    fitness: float = 0.0

    def copy(self):
        """Create a deep copy of chromosome"""
        return Chromosome(
            genes=[Gene(g.order_id, g.driver_id, g.queue_position) for g in self.genes],
            fitness=self.fitness
        )


class GeneticScheduler:
    """Genetic Algorithm for optimizing driver-order assignments"""

    def __init__(self):
        self.settings = get_settings()
        self.population_size = self.settings.GA_POPULATION_SIZE
        self.generations = self.settings.GA_GENERATIONS
        self.mutation_rate = self.settings.GA_MUTATION_RATE
        self.crossover_rate = self.settings.GA_CROSSOVER_RATE
        self.elite_size = self.settings.GA_ELITE_SIZE
        self.tournament_size = self.settings.GA_TOURNAMENT_SIZE

        # Scheduling constraints
        self.max_orders_per_driver = self.settings.MAX_ORDERS_PER_DRIVER

        # Fitness weights
        self.priority_weight = self.settings.PRIORITY_WEIGHT
        self.distance_weight = self.settings.DISTANCE_WEIGHT
        self.balance_weight = self.settings.BALANCE_WEIGHT

    def optimize(
            self,
            drivers: List[Driver],
            orders: List[OrderDetail]
    ) -> Dict[UUID, List[UUID]]:
        """
        Main optimization function using Genetic Algorithm

        Returns:
            Dict mapping driver_id to list of order_ids
        """
        if not drivers or not orders:
            return {}

        # Initialize population
        population = self._initialize_population(drivers, orders)

        # Calculate fitness for initial population
        for chromosome in population:
            chromosome.fitness = self._calculate_fitness(chromosome, drivers, orders)

        # Evolution loop
        best_solution = None
        best_fitness = float('-inf')

        for generation in range(self.generations):
            # Sort by fitness
            population.sort(key=lambda x: x.fitness, reverse=True)

            # Track best solution
            if population[0].fitness > best_fitness:
                best_fitness = population[0].fitness
                best_solution = population[0].copy()

            # Create new population
            new_population = []

            # Elitism: Keep best solutions
            new_population.extend([chrom.copy() for chrom in population[:self.elite_size]])

            # Generate offspring
            while len(new_population) < self.population_size:
                # Selection
                parent1 = self._tournament_selection(population)
                parent2 = self._tournament_selection(population)

                # Crossover
                if random.random() < self.crossover_rate:
                    offspring1, offspring2 = self._crossover(parent1, parent2)
                else:
                    offspring1, offspring2 = parent1.copy(), parent2.copy()

                # Mutation
                if random.random() < self.mutation_rate:
                    offspring1 = self._mutate(offspring1, drivers)
                if random.random() < self.mutation_rate:
                    offspring2 = self._mutate(offspring2, drivers)

                # Repair and evaluate
                offspring1 = self._repair_chromosome(offspring1, drivers, orders)
                offspring2 = self._repair_chromosome(offspring2, drivers, orders)

                offspring1.fitness = self._calculate_fitness(offspring1, drivers, orders)
                offspring2.fitness = self._calculate_fitness(offspring2, drivers, orders)

                new_population.extend([offspring1, offspring2])

            population = new_population[:self.population_size]

        # Convert best solution to result format
        return self._chromosome_to_schedule(best_solution, drivers, orders)

    def _initialize_population(
            self,
            drivers: List[Driver],
            orders: List[OrderDetail]
    ) -> List[Chromosome]:
        """Initialize random population"""
        population = []

        for _ in range(self.population_size):
            genes = []
            available_drivers = [d.id for d in drivers]
            driver_order_counts = {d.id: 0 for d in drivers}

            # Shuffle orders for randomness
            shuffled_orders = random.sample(orders, len(orders))

            for order in shuffled_orders:
                # Select random available driver
                valid_drivers = [
                    d_id for d_id in available_drivers
                    if driver_order_counts[d_id] < self.max_orders_per_driver
                ]

                if not valid_drivers:
                    # All drivers at capacity, use any driver
                    valid_drivers = available_drivers

                selected_driver = random.choice(valid_drivers)
                queue_pos = driver_order_counts[selected_driver]

                genes.append(Gene(
                    order_id=order.id,
                    driver_id=selected_driver,
                    queue_position=queue_pos
                ))

                driver_order_counts[selected_driver] += 1

            population.append(Chromosome(genes=genes))

        return population

    def _calculate_fitness(
            self,
            chromosome: Chromosome,
            drivers: List[Driver],
            orders: List[OrderDetail]
    ) -> float:
        """
        Calculate fitness score for a chromosome
        Higher score = better solution

        Fitness considers:
        1. Priority satisfaction (high priority orders assigned)
        2. Distance optimization (orders in same area to same driver)
        3. Load balancing (equal distribution among drivers)
        """
        # Create lookup dictionaries
        driver_dict = {d.id: d for d in drivers}
        order_dict = {o.id: o for o in orders}

        # Group genes by driver
        driver_assignments = {}
        for gene in chromosome.genes:
            if gene.driver_id not in driver_assignments:
                driver_assignments[gene.driver_id] = []
            driver_assignments[gene.driver_id].append(gene.order_id)

        # 1. Priority Score
        priority_score = 0
        for gene in chromosome.genes:
            order = order_dict.get(gene.order_id)
            if order:
                priority_score += order.get_priority()

        # Normalize priority score
        max_priority = sum(o.get_priority() for o in orders)
        priority_score = priority_score / max_priority if max_priority > 0 else 0

        # 2. Distance Score (area clustering)
        distance_score = 0
        for driver_id, order_ids in driver_assignments.items():
            driver = driver_dict.get(driver_id)
            if not driver:
                continue

            # Count orders in driver's expertise area
            same_area_count = 0
            for order_id in order_ids:
                order = order_dict.get(order_id)
                if order and driver.area_expertise:
                    if order.area_code == driver.area_expertise:
                        same_area_count += 1

            # Reward for clustered orders
            if len(order_ids) > 0:
                distance_score += same_area_count / len(order_ids)

        # Normalize distance score
        num_drivers = len(driver_assignments)
        distance_score = distance_score / num_drivers if num_drivers > 0 else 0

        # 3. Load Balance Score
        order_counts = [len(orders) for orders in driver_assignments.values()]
        if order_counts:
            mean_orders = np.mean(order_counts)
            std_orders = np.std(order_counts)
            # Lower standard deviation = better balance
            balance_score = 1 / (1 + std_orders) if std_orders > 0 else 1.0
        else:
            balance_score = 0

        # 4. Capacity Penalty
        capacity_penalty = 0
        for driver_id, order_ids in driver_assignments.items():
            if len(order_ids) > self.max_orders_per_driver:
                excess = len(order_ids) - self.max_orders_per_driver
                capacity_penalty += excess * 0.1

        # Combined fitness
        fitness = (
                self.priority_weight * priority_score +
                self.distance_weight * distance_score +
                self.balance_weight * balance_score -
                capacity_penalty
        )

        return fitness

    def _tournament_selection(self, population: List[Chromosome]) -> Chromosome:
        """Select parent using tournament selection"""
        tournament = random.sample(population, self.tournament_size)
        return max(tournament, key=lambda x: x.fitness)

    def _crossover(
            self,
            parent1: Chromosome,
            parent2: Chromosome
    ) -> Tuple[Chromosome, Chromosome]:
        """Perform single-point crossover"""
        if len(parent1.genes) <= 1:
            return parent1.copy(), parent2.copy()

        crossover_point = random.randint(1, len(parent1.genes) - 1)

        offspring1_genes = (
                parent1.genes[:crossover_point] +
                parent2.genes[crossover_point:]
        )
        offspring2_genes = (
                parent2.genes[:crossover_point] +
                parent1.genes[crossover_point:]
        )

        return (
            Chromosome(genes=offspring1_genes),
            Chromosome(genes=offspring2_genes)
        )

    def _mutate(self, chromosome: Chromosome, drivers: List[Driver]) -> Chromosome:
        """Mutate chromosome by randomly changing driver assignments"""
        if not chromosome.genes:
            return chromosome

        mutated = chromosome.copy()
        mutation_point = random.randint(0, len(mutated.genes) - 1)

        # Change driver assignment
        available_drivers = [d.id for d in drivers]
        new_driver = random.choice(available_drivers)

        mutated.genes[mutation_point].driver_id = new_driver

        return mutated

    def _repair_chromosome(
            self,
            chromosome: Chromosome,
            drivers: List[Driver],
            orders: List[OrderDetail]
    ) -> Chromosome:
        """
        Repair chromosome to ensure:
        1. Each order appears exactly once
        2. Queue positions are valid
        """
        # Ensure all orders are present
        order_ids = {o.id for o in orders}
        existing_orders = {g.order_id for g in chromosome.genes}

        # Add missing orders
        missing_orders = order_ids - existing_orders
        if missing_orders:
            for order_id in missing_orders:
                driver = random.choice(drivers)
                chromosome.genes.append(Gene(
                    order_id=order_id,
                    driver_id=driver.id,
                    queue_position=0
                ))

        # Remove duplicate orders
        seen_orders = set()
        unique_genes = []
        for gene in chromosome.genes:
            if gene.order_id not in seen_orders:
                seen_orders.add(gene.order_id)
                unique_genes.append(gene)

        chromosome.genes = unique_genes

        # Fix queue positions
        driver_queues = {}
        for gene in chromosome.genes:
            if gene.driver_id not in driver_queues:
                driver_queues[gene.driver_id] = 0
            gene.queue_position = driver_queues[gene.driver_id]
            driver_queues[gene.driver_id] += 1

        return chromosome

    def _chromosome_to_schedule(
            self,
            chromosome: Chromosome,
            drivers: List[Driver],
            orders: List[OrderDetail]
    ) -> Dict[UUID, List[UUID]]:
        """Convert chromosome to schedule format"""
        schedule = {driver.id: [] for driver in drivers}

        # Group by driver and sort by queue position
        driver_genes = {}
        for gene in chromosome.genes:
            if gene.driver_id not in driver_genes:
                driver_genes[gene.driver_id] = []
            driver_genes[gene.driver_id].append(gene)

        # Sort each driver's orders by queue position
        for driver_id, genes in driver_genes.items():
            sorted_genes = sorted(genes, key=lambda x: x.queue_position)
            schedule[driver_id] = [g.order_id for g in sorted_genes]

        return schedule