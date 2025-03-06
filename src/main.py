import neat
import json
import pygame
from simulation import Simulation
from koi import Koi

print("Starting Koi Pond Simulation...")

def run_simulation():
    # Initialize pygame
    pygame.init()
    
    # Load configuration
    with open('config/simulation-config.json') as f:
        sim_config = json.load(f)
     # Set up display
    screen_width = sim_config['screen_width']
    screen_height = sim_config['screen_height'] 
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("Koi Pond Simulation")

    # Load NEAT configuration
    config_path = 'config/neat-config.ini'
    config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                         neat.DefaultSpeciesSet, neat.DefaultStagnation,
                         config_path)

    # Initialize scoreboard
    from scoreboard import Scoreboard
    Scoreboard.initialize()

    # Create the simulation
    simulation = Simulation(config, sim_config)
    
    try:
        simulation.run()
    except KeyboardInterrupt:
        print("\nSimulation stopped by user")
    except Exception as e:
        print(f"Error in simulation: {e}")
        import traceback
        traceback.print_exc()
    finally:
        pygame.quit()

if __name__ == '__main__':
    run_simulation()
