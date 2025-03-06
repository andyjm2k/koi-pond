# Koi Pond Simulation Tests

This directory contains tests for the Koi Pond Simulation project.

## Running Tests

There are several ways to run the tests:

### 1. Using the run_tests.py script

From the project root directory, run:

```bash
python run_tests.py
```

This will discover and run all tests in the tests directory.

### 2. Using unittest directly

From the project root directory, run:

```bash
python -m unittest discover -s tests
```

### 3. Running individual test files

To run a specific test file, use:

```bash
python -m unittest tests.test_simulation
```

## Test Coverage

The tests cover all methods in the simulation.py file:

- `__init__`: Tests initialization with different config options
- `spawn_lily_pads`: Tests the lily pad spawning logic
- `eval_genomes`: Tests the genome evaluation process
- `run`: Tests the main simulation run method
- `evaluate_generation`: Tests the generation evaluation logic

## Mocked Dependencies

The tests use mock objects for the following dependencies:

- NEAT library (Population, StdOutReporter, etc.)
- Koi class
- LilyPad class
- Renderer class
- Scoreboard class

This allows the tests to run without requiring actual neural networks or graphics rendering. 