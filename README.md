# Koi Pond Simulation

This project simulates the genetic evolution of koi fish in a virtual pond using the NEAT algorithm. Koi compete for survival by feeding on lily pads and interacting with each other, developing traits to gain advantages in their environment.

## Features

- Configurable simulation parameters
- Visual rendering of the koi pond
- Genetic evolution using NEAT
- Schooling behavior among koi of the same species
- Dynamic ecosystem with lily pads as food sources

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the simulation:
   ```bash
   python src/main.py
   ```

## Configuration

- `config/neat-config.ini`: NEAT algorithm settings
- `config/simulation-config.json`: Simulation parameters including pond size, number of lily pads, and koi properties

## License

MIT License
