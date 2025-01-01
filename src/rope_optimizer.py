import random
import pygame

class RopeOptimizer:
    def __init__(self, window_size, num_of_ropes, start_area, end_area):
        self.window_size = window_size
        self.num_of_ropes = num_of_ropes
        self.start_area = start_area
        self.end_area = end_area

    def init_population(self):
        population = []
        for _ in range(100):
            rope_config = [
                (random.randint(50, self.window_size[0] - 50), random.randint(50, self.window_size[1] - 100),
                 random.randint(3, 7), random.randint(30, 35))
                for _ in range(self.num_of_ropes)
            ]
            population.append(rope_config)
        return population

    def fitness(self, ropes):
        score = 0
        for (x, y, length, points) in ropes:
            rope_range = length * points
            # Calculate the effective area the rope can reach
            rope_end_pos = pygame.Rect(x - rope_range, y - rope_range, rope_range * 2, rope_range * 2)
            
            # Penalize if a rope can reach the safe zones
            if self.start_area.colliderect(rope_end_pos):
                score -= 100  # Heavily penalize overlapping with the start area
            elif self.end_area.colliderect(rope_end_pos):
                score -= 100  # Heavily penalize overlapping with the end area
            else:
                score += 1  # Reward configuration that doesn't interfere

        # Check reachability (this is still a placeholder)
        path_clear = self.is_path_clear(ropes)
        if path_clear:
            score += 100

        return score

    def is_path_clear(self, rope_config):
        # Implement a pathfinding algorithm to ensure there is always a path from start to end
        return True

    def evolve(self):
        population = self.init_population()
        
        for _ in range(1000):
            population = sorted(population, key=self.fitness, reverse=True)
            selected = population[:20]

            new_population = []
            while len(new_population) < 100:
                parent1, parent2 = random.sample(selected, 2)
                crossover_point = random.randint(0, self.num_of_ropes - 1)
                child1 = parent1[:crossover_point] + parent2[crossover_point:]
                child2 = parent2[:crossover_point] + parent1[crossover_point:]
                
                if random.random() < 0.1:
                    rope_idx = random.randint(0, self.num_of_ropes - 1)
                    child1[rope_idx] = self.mutate(child1[rope_idx])
                if random.random() < 0.1:
                    rope_idx = random.randint(0, self.num_of_ropes - 1)
                    child2[rope_idx] = self.mutate(child2[rope_idx])
                
                new_population.extend([child1, child2])

            population = new_population
        
        return population[0]

    def mutate(self, rope):
        x, y, length, points = rope
        x = min(max(50, x + random.randint(-10, 10)), self.window_size[0] - 50)
        y = min(max(50, y + random.randint(-10, 10)), self.window_size[1] - 100)
        length = random.randint(3, 7)
        points = random.randint(30, 35)
        return x, y, length, points

def generate_optimized_ropes(window_size, num_of_ropes, start_area, end_area):
    optimizer = RopeOptimizer(window_size, num_of_ropes, start_area, end_area)
    return optimizer.evolve()