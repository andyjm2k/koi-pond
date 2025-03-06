import unittest
from unittest.mock import patch, MagicMock, mock_open, call
import sys
import os
import json
import random

# Add the src directory to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

# Import the module under test
from simulation import Simulation

class TestSimulation(unittest.TestCase):
    """Tests for the Simulation class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create common test data
        self.neat_config = MagicMock()
        self.sim_config = {
            'environment_width': 800,
            'environment_height': 600,
            'num_lily_pads': 20,
            'detection_radius': 100,
            'simulation_steps': 50,
            'num_generations': 5,
            'render': False,
            'boundary_penalty': 0.5
        }
        
        # Set up mock for LilyPad
        self.lily_pad_patcher = patch('simulation.LilyPad', side_effect=lambda x, y: MagicMock())
        self.mock_lily_pad = self.lily_pad_patcher.start()
        
        # Set up mock for Scoreboard - by patching at the module level
        self.scoreboard_patcher = patch('scoreboard.Scoreboard')
        self.mock_scoreboard = self.scoreboard_patcher.start()
        
        # Configure Scoreboard mock
        self.mock_scoreboard._species_records = {}
        self.mock_scoreboard.record_species = MagicMock()
        
    def tearDown(self):
        """Clean up after tests."""
        self.lily_pad_patcher.stop()
        self.scoreboard_patcher.stop()

    @patch('random.randint', side_effect=[10, 20, 30, 40])
    def test_spawn_lily_pads(self, mock_randint):
        """Test the spawn_lily_pads method."""
        # Create simulation with only 2 lily pads for easier testing
        config = dict(self.sim_config)
        config['num_lily_pads'] = 2
        sim = Simulation(self.neat_config, config)
        
        # Clear lily pads and spawn new ones
        sim.lily_pads = []
        
        # Reset mock_lily_pad to track new calls
        self.mock_lily_pad.reset_mock()
        
        # Set up new random values
        mock_randint.side_effect = [50, 60, 70, 80]
        
        # Call the method
        sim.spawn_lily_pads()
        
        # Check lily pad count
        self.assertEqual(len(sim.lily_pads), 2)
        
        # Check LilyPad was called correctly
        expected_calls = [
            call(50, 60),
            call(70, 80)
        ]
        self.mock_lily_pad.assert_has_calls(expected_calls, any_order=True)

    def test_environment_config(self):
        """Test environment_config is correctly created."""
        sim = Simulation(self.neat_config, self.sim_config)
        
        # Check environment config
        self.assertEqual(sim.environment_config['width'], 800)
        self.assertEqual(sim.environment_config['height'], 600)
        self.assertEqual(sim.environment_config['boundary_penalty'], 0.5)
        self.assertEqual(sim.environment_config['detection_radius'], 100)

    @patch('neat.Population')
    @patch('neat.StdOutReporter')
    @patch('neat.StatisticsReporter')
    @patch('neat.Checkpointer')
    @patch('builtins.open', new_callable=mock_open)
    @patch('pickle.dump')
    def test_run_method(self, mock_pickle_dump, mock_open, mock_checkpointer,
                        mock_stats_reporter, mock_stdout_reporter, mock_population):
        """Test the run method."""
        # Setup Population mock
        mock_pop_instance = MagicMock()
        mock_winner = MagicMock()
        mock_pop_instance.run.return_value = mock_winner
        mock_population.return_value = mock_pop_instance
        
        # Create simulation
        sim = Simulation(self.neat_config, self.sim_config)
        
        # Mock eval_genomes to avoid execution
        sim.eval_genomes = MagicMock()
        
        # Run the method
        sim.run()
        
        # Check Population creation
        mock_population.assert_called_once_with(self.neat_config)
        
        # Check reporter usage
        mock_pop_instance.add_reporter.assert_any_call(mock_stdout_reporter.return_value)
        mock_pop_instance.add_reporter.assert_any_call(mock_stats_reporter.return_value)
        mock_pop_instance.add_reporter.assert_any_call(mock_checkpointer.return_value)
        
        # Check population run
        mock_pop_instance.run.assert_called_once_with(sim.eval_genomes, 5)
        
        # Check winner was saved
        mock_open.assert_called_once_with('best_koi.pkl', 'wb')
        mock_pickle_dump.assert_called_once_with(mock_winner, mock_open.return_value.__enter__.return_value)

    def test_evaluate_generation(self):
        """Test evaluate_generation method."""
        # Create mock koi fish
        mock_koi1 = MagicMock()
        mock_koi1.calculate_fitness.return_value = 75.0
        mock_koi1.energy = 90.0
        
        mock_koi2 = MagicMock()
        mock_koi2.calculate_fitness.return_value = 50.0
        mock_koi2.energy = 80.0
        
        koi_list = [mock_koi2, mock_koi1]  # Out of order to test sorting
        
        # Create simulation
        sim = Simulation(self.neat_config, self.sim_config)
        
        # Call evaluate_generation
        sim.evaluate_generation(koi_list, 1)
        
        # Check calculate_fitness calls
        mock_koi1.calculate_fitness.assert_called()
        mock_koi2.calculate_fitness.assert_called()
        
        # Test with renderer
        sim.renderer = MagicMock()
        sim.evaluate_generation(koi_list, 1)
        
        # Check renderer call
        sim.renderer.set_generation.assert_called_once_with(1)

if __name__ == '__main__':
    unittest.main() 