import pygame

class Scoreboard:
    """Scoreboard to track the best performing koi species throughout the simulation."""
    
    _species_records = {}
    _initialized = False
    
    @classmethod
    def initialize(cls):
        """Initialize the scoreboard."""
        cls._species_records = {}
        cls._initialized = True
    
    @classmethod
    def record_species(cls, species_id, koi, fitness, generation, config):
        """Record information about a koi species in the scoreboard."""
        # Use existing scientific name or generate a new one
        scientific_name = None
        if species_id in cls._species_records:
            scientific_name = cls._species_records[species_id]['scientific_name']
        else:
            from koi import Koi
            scientific_name = Koi.generate_scientific_name()
            
        # Get the visual properties directly from the koi
        size = koi.get_radius() * 2  # Convert radius to diameter for size
        
        # Record the species information
        cls._species_records[species_id] = {
            'scientific_name': scientific_name,
            'highest_fitness': fitness,
            'first_generation': cls._species_records.get(species_id, {}).get('first_generation', generation),
            'last_generation': generation,
            'size': size,
            'generation_history': cls._species_records.get(species_id, {}).get('generation_history', []) + [(generation, fitness)]
        }
        
        return cls._species_records[species_id]
    
    @classmethod
    def get_records(cls):
        """Get all recorded species information."""
        return cls._species_records
    
    @classmethod
    def get_species_record(cls, species_id):
        """Get information about a specific species."""
        return cls._species_records.get(species_id)
    
    @classmethod
    def reset(cls):
        """Reset the scoreboard."""
        cls._species_records = {}
        cls._initialized = False
        
    @classmethod
    def get_top_species(cls, n=5):
        """Get the top n species by fitness."""
        sorted_species = sorted(
            cls._species_records.items(),
            key=lambda x: x[1]['highest_fitness'],
            reverse=True
        )
        return sorted_species[:n]