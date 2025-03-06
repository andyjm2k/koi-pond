import neat
import pygame
from koi import Koi
from food import LilyPad
import random
import json

class Simulation:
    def __init__(self, neat_config, sim_config):
        # Store NEAT config
        self.neat_config = neat_config
        
        # Load simulation configuration
        if isinstance(sim_config, str):
            # If sim_config is a file path, load it
            with open(sim_config, 'r') as f:
                self.sim_config = json.load(f)
        else:
            # If sim_config is already a dictionary, use it directly
            self.sim_config = sim_config
        
        # Verify lily pad configuration
        if 'num_lily_pads' not in self.sim_config:
            self.sim_config['num_lily_pads'] = 30  # More lily pads
        print(f"Configured for {self.sim_config['num_lily_pads']} lily pads")  # Debug print
        
        # Initialize lily pads
        self.lily_pads = []
        self.spawn_lily_pads()
        
        # Initialize renderer if rendering is enabled
        self.renderer = None
        if self.sim_config.get('render', False):
            from renderer import Renderer
            screen_size = max(
                self.sim_config['environment_width'],
                self.sim_config['environment_height']
            )
            self.renderer = Renderer(screen_size)
        
        # Add this line to store environment configuration
        self.environment_config = {
            'width': self.sim_config['environment_width'],
            'height': self.sim_config['environment_height'],
            'boundary_penalty': self.sim_config.get('boundary_penalty', 0.5),
            'detection_radius': self.sim_config['detection_radius']
        }
        
        # Remove redundant width/height since we have environment_width/height
        # Remove redundant food_count since we have num_lily_pads
        
        # Get simulation attributes from config
        self.simulation_steps = self.sim_config['simulation_steps']
        self.detection_radius = self.sim_config['detection_radius']
        self.num_generations = self.sim_config['num_generations']
        
        # Initialize the scoreboard at simulation start
        from scoreboard import Scoreboard
        Scoreboard._species_records = {}  # Reset species records
        
        # Store the population reference
        self.population = None

    def spawn_lily_pads(self):
        # Clear any existing lily pads
        self.lily_pads = []
        
        # Spawn new lily pads
        num_lily_pads = self.sim_config.get('num_lily_pads', 30)
        for _ in range(num_lily_pads):
            x = random.randint(0, self.sim_config['environment_width'])
            y = random.randint(0, self.sim_config['environment_height'])
            self.lily_pads.append(LilyPad(x, y))
        
        print(f"Spawned {len(self.lily_pads)} lily pads")

    def eval_genomes(self, genomes, config):
        """Evaluate genomes by creating koi fish and running them in the simulation."""
        # Create koi for each genome
        koi_list = []
        genome_to_koi = {}
        
        print("\n=== Creating Koi Fish ===")
        # Create koi for each genome
        for genome_id, genome in genomes:
            # Initialize genome fitness to 0
            genome.fitness = 0
            
            # Get the species for this genome
            species_id = 0  # Default species ID if not available
            if hasattr(self, 'population') and self.population and hasattr(self.population.species, 'get_species_id'):
                try:
                    species_id = self.population.species.get_species_id(genome_id)
                except Exception as e:
                    print(f"Could not get species ID: {e}")
            
            print(f"Creating koi for genome {genome_id} (Species {species_id})")
            
            # Create a new koi with random position
            position = (
                random.randint(50, self.environment_config['width'] - 50),
                random.randint(50, self.environment_config['height'] - 50)
            )
            
            koi_fish = Koi(
                genome=genome,
                config=config,
                position=position,
                environment_config=self.environment_config,
                species_id=species_id
            )
            
            koi_list.append(koi_fish)
            genome_to_koi[genome_id] = koi_fish
            genome.koi = koi_fish
        
        # Run simulation for multiple trials
        num_trials = 1  # Can be increased for more robust evaluation
        print(f"\n=== Running {num_trials} trials ===")
        
        for trial in range(num_trials):
            # Reset environment and koi
            self.spawn_lily_pads()
            for koi in koi_list:
                koi.reset(self.sim_config)
                
            # Run simulation for specified steps
            for step in range(self.sim_config['simulation_steps']):
                for koi in koi_list[:]:  # Copy to allow removal during iteration
                    if koi not in koi_list:
                        continue  # Skip koi that have been removed
                        
                    detection_radius = self.sim_config['detection_radius']
                    nearby_lily_pads = [pad for pad in self.lily_pads if koi.distance_to(pad) < detection_radius]
                    nearby_koi = [other for other in koi_list if other != koi and koi.distance_to(other) < detection_radius]
                    
                    koi.take_action(nearby_lily_pads, nearby_koi)
                    koi.update(self.lily_pads, koi_list)
                
                # Render current state
                if self.renderer:
                    try:
                        if not self.renderer.render(koi_list, self.lily_pads):
                            return  # Exit if window is closed
                    except Exception as e:
                        print(f"Warning: Rendering error occurred: {e}")
                        import traceback
                        traceback.print_exc()
                        # Continue simulation despite rendering error
            
            # Calculate fitness for each genome
            for genome_id, genome in genomes:
                koi_fish = genome_to_koi.get(genome_id)
                if koi_fish and koi_fish in koi_list:
                    trial_fitness = koi_fish.calculate_fitness()
                    
                    # Add to genome fitness (averaged across trials)
                    genome.fitness += trial_fitness / num_trials
                    
                    # Store the koi's highest fitness in the genome
                    if not hasattr(genome, 'highest_fitness'):
                        genome.highest_fitness = 0
                    genome.highest_fitness = max(genome.highest_fitness, koi_fish.highest_fitness)
            
            # Remove koi references from genomes before finishing
            for _, genome in genomes:
                if hasattr(genome, 'koi'):
                    delattr(genome, 'koi')
                    
        # Display the best koi from this generation
        if koi_list:
            best_koi = max(koi_list, key=lambda k: k.highest_fitness)
            print(f"\n=== Best Koi This Generation ===")
            print(f"Species ID: {best_koi.species_id}")
            print(f"Highest Fitness: {best_koi.highest_fitness}")
            
            # Record the best performing species
            from scoreboard import Scoreboard
            species_id = str(best_koi.species_id)
            
            # Record in scoreboard
            Scoreboard.record_species(
                species_id=species_id,
                koi=best_koi,
                fitness=best_koi.highest_fitness,
                generation=self.population.generation,
                config=config
            )

    def run(self):
        """Run the NEAT algorithm to evolve a network to solve the task."""
        # Create the population
        population = neat.Population(self.neat_config)
        
        # Store the population for use in eval_genomes
        self.population = population
        
        # Add a reporter to show progress in the terminal
        population.add_reporter(neat.StdOutReporter(True))
        stats = neat.StatisticsReporter()
        population.add_reporter(stats)
        
        # Set up checkpoint every 10 generations
        population.add_reporter(neat.Checkpointer(10))
        
        # Run for up to n generations
        num_generations = self.sim_config.get('num_generations', 100)
        winner = population.run(self.eval_genomes, num_generations)
        
        # Display the winning genome
        print('\nBest genome:\n{!s}'.format(winner))
        
        # Save the best genome
        with open('best_koi.pkl', 'wb') as f:
            import pickle
            pickle.dump(winner, f)
            
        print("Saved the best koi genome to 'best_koi.pkl'")
        
    def evaluate_generation(self, koi_list, generation):
        """Evaluate the performance of each koi in the generation."""
        # Sort koi by fitness
        koi_list.sort(key=lambda k: k.calculate_fitness(), reverse=True)
        
        # Print top 5 performers
        if len(koi_list) > 0:
            print(f"\nGeneration {generation} results:")
            for i, koi in enumerate(koi_list[:5]):
                fitness = koi.calculate_fitness()
                print(f"  #{i+1}: Fitness {fitness:.2f}, Energy: {koi.energy:.2f}")
                
        # If we have a renderer, update the generation count
        if self.renderer:
            self.renderer.set_generation(generation)