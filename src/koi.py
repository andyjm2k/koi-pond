import math
import neat
import random

class Koi:
    def __init__(self, genome, config, position, environment_config, species_id=None):
        self.genome = genome
        self.config = config
        self.network = neat.nn.FeedForwardNetwork.create(genome, config)
        self.environment_config = environment_config
        self.position = position
        self.last_position = position
        self.hunger = 0
        self.energy = 100
        self.species_id = species_id
        self.highest_fitness = 0
        self.scientific_name = self.generate_scientific_name()

    def take_action(self, nearby_lily_pads, nearby_koi):
        # Store previous position for smooth movement
        self.last_position = self.position
        
        if self.hunger >= 200:  # Koi dies if too hungry
            return
            
        # Get inputs for the neural network
        inputs = self.get_inputs(nearby_lily_pads, nearby_koi)
        
        # Get outputs from neural network
        outputs = self.network.activate(inputs)
        
        # The NEAT config specifies 5 outputs
        # Interpret outputs as movement direction, speed, and other behaviors
        direction_x = outputs[0]
        direction_y = outputs[1]
        speed = abs(outputs[2])  # Use absolute value to ensure positive speed
        
        # Normalize direction vector
        magnitude = math.sqrt(direction_x**2 + direction_y**2)
        if magnitude > 0:
            direction_x /= magnitude
            direction_y /= magnitude
        
        # Apply movement
        max_speed = 5.0
        actual_speed = speed * max_speed
        
        # Update position
        self.position = (
            self.position[0] + direction_x * actual_speed,
            self.position[1] + direction_y * actual_speed
        )
        
        # Increase hunger proportionally to movement
        movement_cost = self.distance_to((self.last_position[0], self.last_position[1])) * 0.1
        self.hunger += movement_cost
        
        # Constrain position to environment boundaries
        self.position = (
            max(0, min(self.environment_config['width'], self.position[0])),
            max(0, min(self.environment_config['height'], self.position[1]))
        )
    
    def get_closest_lily_pad_info(self, nearby_lily_pads):
        # Default values if no lily pads are nearby
        result = {
            'distance': self.environment_config['detection_radius'],
            'direction_x': 0,
            'direction_y': 0
        }
        
        if not nearby_lily_pads:
            return result
            
        # Find the closest lily pad
        closest_lily_pad = min(nearby_lily_pads, key=lambda pad: self.distance_to(pad))
        distance = self.distance_to(closest_lily_pad)
        
        # Calculate direction to the closest lily pad
        if distance > 0:
            direction_x = (closest_lily_pad.position[0] - self.position[0]) / distance
            direction_y = (closest_lily_pad.position[1] - self.position[1]) / distance
        else:
            direction_x = 0
            direction_y = 0
            
        return {
            'distance': distance,
            'direction_x': direction_x,
            'direction_y': direction_y
        }

    def get_inputs(self, nearby_lily_pads, nearby_koi):
        # Get closest lily pad and koi info
        lily_pad_info = self.get_closest_lily_pad_info(nearby_lily_pads)
        koi_info = self.get_closest_koi_info(nearby_koi)
        
        # Calculate schooling behavior
        schooling_x = 0
        schooling_y = 0
        num_neighbors = 0
        
        for other in nearby_koi:
            if other.species_id == self.species_id:
                dx = other.position[0] - self.position[0]
                dy = other.position[1] - self.position[1]
                dist = math.sqrt(dx*dx + dy*dy)
                if dist < 100:  # Schooling radius
                    schooling_x += dx
                    schooling_y += dy
                    num_neighbors += 1
        
        if num_neighbors > 0:
            schooling_x /= num_neighbors
            schooling_y /= num_neighbors
        
        # Normalize inputs - exactly 10 inputs as specified in the NEAT config
        inputs = [
            self.hunger / 200.0,  # Normalized hunger
            self.position[0] / self.environment_config['width'],  # Normalized x position
            self.position[1] / self.environment_config['height'],  # Normalized y position
            lily_pad_info['distance'] / self.environment_config['detection_radius'],  # Normalized distance to lily pad
            lily_pad_info['direction_x'],  # Direction to lily pad (x)
            lily_pad_info['direction_y'],  # Direction to lily pad (y)
            koi_info['distance'] / self.environment_config['detection_radius'],  # Normalized distance to koi
            koi_info['direction_x'],  # Direction to koi (x)
            koi_info['direction_y'],  # Direction to koi (y)
            num_neighbors / 10.0  # Normalized number of neighbors (schooling influence)
        ]
        
        return inputs

    def get_closest_food_info(self, nearby_food):
        if not nearby_food:
            return [1.0, 0.0]  # Max distance, no angle
        
        # Calculate vision cone parameters
        vision_angle = 120  # Must match renderer's vision_angle
        vision_length = 80  # Must match renderer's vision_length
        
        # Get current orientation angle (from velocity)
        if hasattr(self, 'last_position'):
            dx = self.position[0] - self.last_position[0]
            dy = self.position[1] - self.last_position[1]
            if dx != 0 or dy != 0:
                current_angle = math.degrees(math.atan2(dy, dx))
            else:
                current_angle = 0
        else:
            current_angle = 0
        
        # Filter food items to only those in vision cone
        visible_food = []
        for food in nearby_food:
            if food.position is None:
                continue
            
            # Calculate angle and distance to food
            food_dx = food.position[0] - self.position[0]
            food_dy = food.position[1] - self.position[1]
            distance = math.sqrt(food_dx*food_dx + food_dy*food_dy)
            
            if distance > vision_length:
                continue
            
            # Calculate angle to food relative to current orientation
            food_angle = math.degrees(math.atan2(food_dy, food_dx))
            angle_diff = abs((food_angle - current_angle + 180) % 360 - 180)
            
            if angle_diff <= vision_angle/2:
                visible_food.append((food, distance, food_angle))
        
        if not visible_food:
            return [1.0, 0.0]  # Nothing in vision cone
        
        # Get closest visible food
        closest_food, distance, angle = min(visible_food, key=lambda x: x[1])
        
        return [
            min(1.0, distance / vision_length),  # Normalized distance
            (angle - current_angle) / 180.0  # Normalized angle (-1 to 1)
        ]

    def get_closest_koi_info(self, nearby_koi):
        # Default values if no koi are nearby
        result = {
            'distance': self.environment_config['detection_radius'],
            'direction_x': 0,
            'direction_y': 0
        }
        
        if not nearby_koi:
            return result
            
        # Find the closest koi
        closest_koi = min(nearby_koi, key=lambda k: self.distance_to(k))
        distance = self.distance_to(closest_koi)
        
        # Calculate direction to the closest koi
        if distance > 0:
            direction_x = (closest_koi.position[0] - self.position[0]) / distance
            direction_y = (closest_koi.position[1] - self.position[1]) / distance
        else:
            direction_x = 0
            direction_y = 0
            
        return {
            'distance': distance,
            'direction_x': direction_x,
            'direction_y': direction_y
        }

    def distance_to(self, other):
        """Calculate distance between this koi and another object or position"""
        if self.position is None:
            return float('inf')
            
        # Handle both objects with position attributes and direct position tuples
        other_pos = other
        if hasattr(other, 'position'):
            other_pos = other.position
            
        if other_pos is None:
            return float('inf')
        
        dx = self.position[0] - other_pos[0]
        dy = self.position[1] - other_pos[1]
        return math.sqrt(dx*dx + dy*dy)

    def reset(self, sim_config):
        """Reset koi for a new trial"""
        self.hunger = 0
        self.energy = 100
        self.steps_taken = 0
        self.food_consumed = 0
        self.organisms_consumed = 0
        self.was_moving = False
        # Keep position, species_id, and network intact

    def update(self, lily_pads, other_koi):
        """Update the koi state based on interactions with lily pads and other koi."""
        # Check for lily pad consumption
        for lily_pad in lily_pads[:]:
            if self.distance_to(lily_pad) < 10:  # If close enough to consume
                self.hunger = max(0, self.hunger - 30)  # Reduce hunger
                lily_pads.remove(lily_pad)  # Remove the consumed lily pad
                
        # Increase hunger over time
        self.hunger += 0.1
        
        # Update energy based on hunger
        self.energy = max(0, 100 - self.hunger / 2)
        
        # Calculate and update fitness
        current_fitness = self.calculate_fitness()
        self.highest_fitness = max(self.highest_fitness, current_fitness)

    def calculate_fitness(self):
        """Calculate the fitness of this koi."""
        # Base fitness on energy level and survival time
        fitness = self.energy
        
        return max(0, fitness)

    def get_radius(self):
        """Get the radius of the koi based on its energy."""
        base_radius = 10
        energy_factor = self.energy / 100.0  # Normalize energy to 0-1 range
        return base_radius * max(0.5, min(1.5, energy_factor))  # Scale between 50% and 150% of base radius

    @staticmethod
    def generate_scientific_name():
        """Generate a scientific-sounding name for a koi species."""
        # Prefixes for genus names
        genus_prefixes = [
            "Cyprinus", "Koi", "Nishiki", "Hikari", "Ogon", "Asagi", "Showa", "Kohaku", "Sanke", "Utsurimono",
            "Bekko", "Tancho", "Kinginrin", "Karasugoi", "Chagoi", "Soragoi", "Ochiba", "Goshiki", "Koromo"
        ]
        
        # Suffixes for species names
        species_suffixes = [
            "carpio", "japonicus", "auratus", "elegans", "magnificus", "splendidus", "nobilis",
            "imperialis", "regalis", "spectabilis", "formosus", "ornatus", "picturatus"
        ]
        
        # Generate random genus and species
        import random
        genus = random.choice(genus_prefixes)
        species = random.choice(species_suffixes)
        
        return f"{genus} {species}"