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
        self.steps_taken = 0  # Track how many steps the koi has survived
        self.food_consumed = 0  # Track how many lily pads consumed
        self.movement_efficiency = 0  # Track how efficiently the koi moves

    def __getstate__(self):
        """Return state for pickling, excluding unpicklable objects."""
        state = self.__dict__.copy()
        
        # Remove the neural network object - we can recreate it from genome and config
        if 'network' in state:
            del state['network']
        
        # Clean up any potential pygame references
        # Note: genome might have circular references back to this koi object
        if 'genome' in state and hasattr(state['genome'], 'koi'):
            # Don't store the reference to ourselves in the genome
            state['_has_koi_ref'] = True
            # Store genome key instead of the full genome to avoid circular references
            if hasattr(state['genome'], 'key'):
                state['_genome_key'] = state['genome'].key
            del state['genome']
        
        # Ensure we don't have any pygame references in our environment config
        if 'environment_config' in state:
            # Make a clean copy without any potential pygame references
            clean_env = {}
            for k, v in state['environment_config'].items():
                # Skip any values that might be pygame objects
                if not isinstance(v, (int, float, str, bool, tuple, list, dict)) and v is not None:
                    continue
                clean_env[k] = v
            state['environment_config'] = clean_env
            
        return state
        
    def __setstate__(self, state):
        """Restore state after unpickling."""
        self.__dict__.update(state)
        
        # Neural network will need to be recreated later
        self.network = None
        
        # Genome will need to be reattached later if it had a circular reference
        if '_has_koi_ref' in self.__dict__:
            del self._has_koi_ref
            # We stored the genome key rather than the full genome
            if '_genome_key' in self.__dict__:
                # genome will be reattached by the simulation after loading
                self._need_genome_reattach = True
                self._genome_key = self._genome_key
                del self._genome_key
            
    def restore_network(self, genome=None, config=None):
        """Recreate the neural network after unpickling.
        
        Args:
            genome: The genome to use (if not already available)
            config: The config to use (if not already available)
        """
        if genome is not None:
            self.genome = genome
        
        if config is not None:
            self.config = config
            
        # Recreate the neural network from genome and config
        if hasattr(self, 'genome') and hasattr(self, 'config') and self.genome and self.config:
            try:
                self.network = neat.nn.FeedForwardNetwork.create(self.genome, self.config)
            except Exception as e:
                print(f"Error recreating neural network: {e}")
                self.network = None

    def make_pickle_safe(self):
        """Prepare this object for pickling by removing unpicklable references."""
        # Store any references that might cause issues with pickling
        self._temp_network = self.network
        self.network = None
        
        # Store genome if it has circular references
        if hasattr(self.genome, 'koi') and self.genome.koi is self:
            self._temp_genome = self.genome
            # We'll need to restore this later, so flag it
            self._had_genome_ref = True
            self.genome = None

    def restore_after_pickle(self):
        """Restore the object after pickling."""
        # Restore network reference
        if hasattr(self, '_temp_network'):
            self.network = self._temp_network
            del self._temp_network
        
        # Restore genome reference if it was removed
        if hasattr(self, '_had_genome_ref') and hasattr(self, '_temp_genome'):
            self.genome = self._temp_genome
            del self._temp_genome
            del self._had_genome_ref

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
        schooling_tendency = outputs[3] if len(outputs) > 3 else 0.5  # How much to follow school
        aggression = outputs[4] if len(outputs) > 4 else 0.0  # How aggressive with other koi
        
        # Normalize direction vector
        magnitude = math.sqrt(direction_x**2 + direction_y**2)
        if magnitude > 0:
            direction_x /= magnitude
            direction_y /= magnitude
        
        # Apply schooling behavior based on neural network output
        if nearby_koi and schooling_tendency > 0:
            # Find center of same-species koi
            school_x, school_y, school_count = 0, 0, 0
            for other in nearby_koi:
                if other.species_id == self.species_id:
                    school_x += other.position[0]
                    school_y += other.position[1]
                    school_count += 1
            
            if school_count > 0:
                # Get direction to school center
                school_x /= school_count
                school_y /= school_count
                school_dir_x = school_x - self.position[0]
                school_dir_y = school_y - self.position[1]
                
                # Normalize
                school_mag = math.sqrt(school_dir_x**2 + school_dir_y**2)
                if school_mag > 0:
                    school_dir_x /= school_mag
                    school_dir_y /= school_mag
                    
                # Blend individual direction with schooling direction based on tendency
                direction_x = direction_x * (1 - schooling_tendency) + school_dir_x * schooling_tendency
                direction_y = direction_y * (1 - schooling_tendency) + school_dir_y * schooling_tendency
                
                # Renormalize
                magnitude = math.sqrt(direction_x**2 + direction_y**2)
                if magnitude > 0:
                    direction_x /= magnitude
                    direction_y /= magnitude
        
        # Apply movement
        max_speed = 5.0
        actual_speed = speed * max_speed
        
        # Track previous position for efficiency calculation
        old_position = self.position
        
        # Update position
        self.position = (
            self.position[0] + direction_x * actual_speed,
            self.position[1] + direction_y * actual_speed
        )
        
        # Increase hunger proportionally to movement, but with a smaller factor
        # Reduce the movement cost to prevent excessive hunger increase and energy drop
        movement_distance = self.distance_to((self.last_position[0], self.last_position[1]))
        movement_cost = movement_distance * 0.05  # Reduced from 0.1 to 0.05
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
        
        # Track same species vs different species
        same_species_neighbors = 0
        diff_species_neighbors = 0
        
        for other in nearby_koi:
            dx = other.position[0] - self.position[0]
            dy = other.position[1] - self.position[1]
            dist = math.sqrt(dx*dx + dy*dy)
            
            if dist < 100:  # Schooling radius
                if other.species_id == self.species_id:
                    schooling_x += dx
                    schooling_y += dy
                    same_species_neighbors += 1
                else:
                    diff_species_neighbors += 1
                
                num_neighbors += 1
        
        if same_species_neighbors > 0:
            schooling_x /= same_species_neighbors
            schooling_y /= same_species_neighbors
        
        # Calculate distance from pond edges to help avoid boundaries
        edge_distances = [
            self.position[0],  # Distance to left edge
            self.environment_config['width'] - self.position[0],  # Distance to right edge
            self.position[1],  # Distance to top edge
            self.environment_config['height'] - self.position[1]  # Distance to bottom edge
        ]
        min_edge_distance = min(edge_distances) / max(self.environment_config['width'], self.environment_config['height'])
        
        # Check for concentration of lily pads in different directions
        lily_pad_concentrations = [0, 0, 0, 0]  # left, right, up, down
        for lily_pad in nearby_lily_pads:
            dx = lily_pad.position[0] - self.position[0]
            dy = lily_pad.position[1] - self.position[1]
            
            # Determine the direction quadrant
            if abs(dx) > abs(dy):  # More horizontal than vertical
                if dx < 0:  # Left
                    lily_pad_concentrations[0] += 1
                else:  # Right
                    lily_pad_concentrations[1] += 1
            else:  # More vertical than horizontal
                if dy < 0:  # Up
                    lily_pad_concentrations[2] += 1
                else:  # Down
                    lily_pad_concentrations[3] += 1
        
        # Normalize lily pad concentrations
        max_concentration = max(lily_pad_concentrations) if max(lily_pad_concentrations) > 0 else 1
        lily_pad_concentrations = [c / max_concentration for c in lily_pad_concentrations]
        
        # Normalize inputs - expanded from 10 to include more environmental awareness
        # Core original inputs
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
            num_neighbors / 10.0,  # Normalized number of neighbors (schooling influence)
            
            # Enhanced environmental awareness inputs
            min_edge_distance,  # Distance to closest edge (normalized)
            same_species_neighbors / 10.0,  # Number of same-species neighbors
            diff_species_neighbors / 10.0,  # Number of different-species neighbors
            lily_pad_concentrations[0],  # Lily pad concentration to the left
            lily_pad_concentrations[1],  # Lily pad concentration to the right
            lily_pad_concentrations[2],  # Lily pad concentration above
            lily_pad_concentrations[3],  # Lily pad concentration below
            self.energy / 100.0,  # Current energy level
            self.steps_taken / 1000.0,  # How long the koi has been alive
            self.food_consumed / 20.0  # How much food the koi has eaten
        ]
        
        return inputs  # Return all 20 inputs to match updated NEAT config

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
        self.movement_efficiency = 0
        # Keep position, species_id, and network intact

    def update(self, lily_pads, other_koi):
        """Update the koi state based on interactions with lily pads and other koi."""
        # Increment steps taken
        self.steps_taken += 1
        
        # Check for lily pad consumption
        for lily_pad in lily_pads[:]:
            if self.distance_to(lily_pad) < 10:  # If close enough to consume
                self.hunger = max(0, self.hunger - 30)  # Reduce hunger
                lily_pads.remove(lily_pad)  # Remove the consumed lily pad
                self.food_consumed += 1  # Track food consumption
                
        # Increase hunger over time, but at a reduced rate
        self.hunger += 0.05  # Reduced from 0.1 to 0.05
        
        # Update energy based on hunger, with a more gradual decline
        # Adjust the formula to make energy decrease more slowly
        self.energy = max(0, 100 - self.hunger / 3)  # Changed from /2 to /3 for slower energy reduction
        
        # Calculate and update fitness
        current_fitness = self.calculate_fitness()
        self.highest_fitness = max(self.highest_fitness, current_fitness)

    def calculate_fitness(self):
        """Calculate the fitness of this koi."""
        # Base fitness components
        energy_factor = self.energy  # 0-100 based on energy level
        
        # Survival factor - reward for living longer
        max_steps = 1000.0  # Assuming simulation runs for about 1000 steps
        survival_factor = min(50.0, self.steps_taken / max_steps * 50.0)
        
        # Food gathering factor - reward for finding and consuming food
        food_factor = self.food_consumed * 20.0
        
        # Exploration factor - reward for exploring the environment
        # This encourages koi to move around and not stay in one place
        border_margin = 50  # Distance from edge to consider "edge territory"
        x, y = self.position
        width = self.environment_config['width']
        height = self.environment_config['height']
        
        # Penalty for staying too close to edges
        edge_penalty = 0
        if x < border_margin or x > width - border_margin or y < border_margin or y > height - border_margin:
            edge_penalty = 15
        
        # Calculate total fitness with balanced weights
        fitness = energy_factor + survival_factor + food_factor - edge_penalty
        
        # Return non-negative fitness
        return max(0, fitness)

    def get_radius(self):
        """Get the radius of the koi based on its energy."""
        base_radius = 10
        
        # Set a minimum size regardless of energy to prevent excessive shrinking
        min_size_factor = 0.8  # Minimum size is 80% of base radius
        
        # Normalize energy to 0-1 range with a boost to prevent small fish
        energy_factor = self.energy / 100.0  # Normalize energy to 0-1 range
        
        # Scale between min_size_factor and 150% of base radius
        return base_radius * max(min_size_factor, min(1.5, energy_factor))  

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