import neat
import pygame
from koi import Koi
from food import LilyPad
import random
import json
from weakref import ref
import copy
import gc

class GenerationReporter(neat.reporting.BaseReporter):
    """Reporter that updates visualization after each generation.
    
    Uses weak references to avoid pickling issues with pygame surfaces.
    """
    
    def __init__(self, update_callback):
        """Initialize with a callback function rather than storing the simulation object.
        
        Args:
            update_callback: Function to call with generation number at end of generation
        """
        self.update_callback = update_callback
        self.current_generation = 0
    
    def start_generation(self, generation):
        """Called at the start of a generation.
        
        Args:
            generation: The current generation number
        """
        self.current_generation = generation
    
    def end_generation(self, config, population, species_set):
        """Called at the end of a generation.
        
        Args:
            config: The NEAT configuration
            population: A dictionary of genomes
            species_set: The species set
        """
        # Use the stored generation number - population is a dict, not the Population object
        current_gen = self.current_generation
        
        # Call the update callback with the current generation
        if self.update_callback:
            self.update_callback(current_gen)
            
            # Print confirmation
            print(f"Updated visualization with generation {current_gen}")

class CheckpointReporter(neat.reporting.BaseReporter):
    """Custom checkpoint reporter that handles pygame objects."""
    
    def __init__(self, filename_prefix='neat-checkpoint-', generation_interval=10, simulation=None):
        self.filename_prefix = filename_prefix
        self.generation_interval = generation_interval
        self.current_generation = 0
        self.simulation = simulation
    
    def start_generation(self, generation):
        """Called at the start of a generation."""
        self.current_generation = generation
        
        # Also update the simulation's generation counter
        if self.simulation:
            self.simulation.current_generation = generation
        
    def end_generation(self, config, population, species_set):
        """Called at the end of a generation.
        
        Args:
            config: The NEAT configuration
            population: A dictionary of genomes
            species_set: The species set
        """
        # Use our stored generation count - population is a dict here
        if self.current_generation % self.generation_interval == 0:
            print(f"Saving checkpoint to {self.filename_prefix}{self.current_generation}")
            
            try:
                # Prepare for saving by cleaning up references
                if self.simulation:
                    self.simulation.make_checkpoint_compatible()
                
                # Create deep copies of objects to ensure no pygame references
                population_copy = {}
                for key, genome in population.items():
                    # Create a clean copy of the genome
                    if hasattr(genome, 'koi'):
                        # Store the koi reference temporarily
                        koi_ref = genome.koi
                        # Remove the koi reference to avoid circular references
                        del genome.koi
                        # Create a deep copy without the koi reference
                        genome_copy = copy.deepcopy(genome)
                        # Restore the koi reference to the original genome
                        genome.koi = koi_ref
                        # Add the clean genome copy to our population copy
                        population_copy[key] = genome_copy
                    else:
                        # No koi reference, just make a deep copy
                        population_copy[key] = copy.deepcopy(genome)
                
                # Deep copy the species set (careful with any potential pygame references)
                species_set_copy = copy.deepcopy(species_set)
                
                # Create the checkpoint filename
                filename = f"{self.filename_prefix}{self.current_generation}"
                
                # Save the clean copies
                data = (population_copy, species_set_copy, self.current_generation)
                with open(filename, 'wb') as f:
                    import pickle
                    pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)
                
                print(f"Successfully saved checkpoint for generation {self.current_generation}")
                
                # Force garbage collection to clean up temporary objects
                del population_copy
                del species_set_copy
                gc.collect()
                
            except Exception as e:
                print(f"Error saving checkpoint: {e}")
                import traceback
                traceback.print_exc()
            finally:
                # Restore the simulation object after checkpointing
                if self.simulation:
                    self.simulation.restore_after_checkpoint()

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
        
        # Track current generation separately
        self.current_generation = 0
    
    def update_generation_display(self, generation):
        """Update generation display in renderer and scoreboard.
        
        This is used as a callback for the GenerationReporter.
        """
        # Update our internal generation tracker
        self.current_generation = generation
        
        # Update the renderer's generation counter
        if self.renderer:
            self.renderer.set_generation(generation)
            
        # Update the scoreboard with the current generation
        from scoreboard import Scoreboard
        Scoreboard.set_current_generation(generation)

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
        # Update the renderer's generation counter at the start of evaluation
        if self.renderer:
            self.renderer.set_generation(self.current_generation)
        
        # Create koi for each genome
        koi_list = []
        genome_to_koi = {}
        
        print(f"\n=== Creating Koi Fish (Generation {self.current_generation}) ===")
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
        
        # Store koi list for checkpointing preparation
        self._temp_koi_list = koi_list
        
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
                    
                    # Take action returns False if koi should die
                    koi_alive = koi.take_action(nearby_lily_pads, nearby_koi)
                    if not koi_alive:
                        if koi in koi_list:
                            koi_list.remove(koi)
                            continue  # Skip update for dead koi
                    
                    koi.update(self.lily_pads, koi_list)
                    
                    # Check if koi's energy is depleted or it's too hungry - remove it from simulation
                    if koi.energy <= 0 or koi.hunger >= 200:
                        if koi in koi_list:
                            koi_list.remove(koi)
                
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
            
            # Get the current generation number from our internal tracker
            current_generation = self.current_generation
            print(f"Current Generation: {current_generation}")
            
            # Record in scoreboard with the correct generation number
            Scoreboard.record_species(
                species_id=species_id,
                koi=best_koi,
                fitness=best_koi.highest_fitness,
                generation=current_generation,
                config=config
            )

    def make_checkpoint_compatible(self):
        """Prepare the simulation object for checkpointing.
        
        This temporarily removes references to unpicklable objects.
        """
        try:
            print("Preparing simulation for checkpointing...")
            
            # Store renderer reference to be restored after checkpointing
            self._temp_renderer = self.renderer
            
            # Remove renderer reference during pickling
            self.renderer = None
            
            # Clear out any other potential pygame references
            for koi_fish in getattr(self, '_temp_koi_list', []):
                if hasattr(koi_fish, 'make_pickle_safe'):
                    koi_fish.make_pickle_safe()
            
            # Force garbage collection to clean up any dangling references
            gc.collect()
            
            print("Simulation ready for checkpointing")
        except Exception as e:
            print(f"Error preparing simulation for checkpointing: {e}")
            import traceback
            traceback.print_exc()
        
    def restore_after_checkpoint(self):
        """Restore the simulation object after checkpointing."""
        try:
            print("Restoring simulation after checkpointing...")
            
            # Restore renderer reference
            if hasattr(self, '_temp_renderer'):
                self.renderer = self._temp_renderer
                del self._temp_renderer
            
            # Restore any other objects that were modified
            for koi_fish in getattr(self, '_temp_koi_list', []):
                if hasattr(koi_fish, 'restore_after_pickle'):
                    koi_fish.restore_after_pickle()
            
            print("Simulation restored after checkpointing")
        except Exception as e:
            print(f"Error restoring simulation after checkpointing: {e}")
            import traceback
            traceback.print_exc()

    def run(self):
        """Run the NEAT algorithm to evolve a network to solve the task."""
        try:
            # Create the population
            population = neat.Population(self.neat_config)
            
            # Store the population for use in eval_genomes
            self.population = population
            
            # Add a reporter to show progress in the terminal
            population.add_reporter(neat.StdOutReporter(True))
            stats = neat.StatisticsReporter()
            population.add_reporter(stats)
            
            # Add custom reporter to update visualization after each generation
            # Pass a callback function instead of the simulation object
            population.add_reporter(GenerationReporter(self.update_generation_display))
            
            # Set up custom checkpoint reporter instead of the standard one
            # NOTE: We're using our own custom checkpoint reporter that carefully
            # handles pygame references and avoids serialization issues
            checkpoint_reporter = CheckpointReporter(simulation=self)
            population.add_reporter(checkpoint_reporter)
            
            # Don't use NEAT's built-in checkpointer, as it doesn't handle pygame objects
            # population.add_reporter(neat.Checkpointer(10))
            
            # Reset current generation
            self.current_generation = 0
            
            # Update the scoreboard with the initial generation
            from scoreboard import Scoreboard
            Scoreboard.set_current_generation(self.current_generation)
            
            # If rendering is enabled, update the renderer's generation counter
            if self.renderer:
                self.renderer.set_generation(self.current_generation)
            
            # Run for up to n generations
            num_generations = self.sim_config.get('num_generations', 100)
            winner = population.run(self.eval_genomes, num_generations)
            
            # Display the winning genome
            print('\nBest genome:\n{!s}'.format(winner))
            
            # Save the best genome
            self.save_best_genome(winner)
            
            return winner
        except Exception as e:
            print(f"Error in simulation run: {e}")
            import traceback
            traceback.print_exc()
            return None
        finally:
            # Clean up resources
            self.cleanup()

    def save_best_genome(self, genome):
        """Save the best genome in a way that avoids pygame serialization issues."""
        try:
            print("Saving best genome...")
            
            # Make a clean copy of the genome for serialization
            if hasattr(genome, 'koi'):
                # Store and remove the koi reference temporarily
                koi_ref = genome.koi
                del genome.koi
                
                # Now pickle the genome without the pygame-containing koi
                with open('best_koi.pkl', 'wb') as f:
                    import pickle
                    pickle.dump(genome, f)
                    
                # Restore the reference
                genome.koi = koi_ref
            else:
                # No koi reference, can pickle directly
                with open('best_koi.pkl', 'wb') as f:
                    import pickle
                    pickle.dump(genome, f)
                    
            print("Saved the best koi genome to 'best_koi.pkl'")
        except Exception as e:
            print(f"Error saving best genome: {e}")
            import traceback
            traceback.print_exc()

    def cleanup(self):
        """Clean up resources used by the simulation."""
        # Clear any references to pygame objects
        if hasattr(self, '_temp_renderer'):
            self._temp_renderer = None
        
        # Clear renderer
        if hasattr(self, 'renderer') and self.renderer is not None:
            self.renderer = None
        
        # Clear lily pads
        if hasattr(self, 'lily_pads'):
            self.lily_pads = []

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