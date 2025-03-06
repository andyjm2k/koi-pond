import pygame
import random
import math
import os

class Renderer:
    def __init__(self, size):
        pygame.init()
        
        # Define scoreboard width first
        self.scoreboard_width = 300
        
        # Create single window with extra width for scoreboard
        total_width = size + self.scoreboard_width
        self.screen = pygame.display.set_mode((total_width, size))
        pygame.display.set_caption("Koi Pond Simulation")
        
        # Define scoreboard area as a rect
        self.scoreboard_rect = pygame.Rect(size, 0, self.scoreboard_width, size)
        
        self.clock = pygame.time.Clock()
        self.generation = 0
        self.species_colors = {}  # Dictionary to store colors for each species
        print(f"Renderer initialized with screen size: {size}x{size}")

        # Enhanced fonts and colors
        pygame.font.init()
        try:
            self.title_font = pygame.font.Font('assets/fonts/Roboto-Bold.ttf', 36)
            self.header_font = pygame.font.Font('assets/fonts/Roboto-Medium.ttf', 28)
            self.font = pygame.font.Font('assets/fonts/Roboto-Regular.ttf', 20)
        except:
            print("Falling back to default font")
            self.title_font = pygame.font.Font(None, 36)
            self.header_font = pygame.font.Font(None, 28)
            self.font = pygame.font.Font(None, 20)

        # Koi pond color scheme
        self.colors = {
            'water': (68, 108, 162),      # Deep blue water
            'ripple': (82, 121, 174),     # Lighter blue for ripples
            'title': (255, 255, 255),     # White text
            'text': (220, 220, 220),      # Light grey text
            'highlight': (255, 183, 77),  # Golden highlight
            'card': (51, 77, 122),        # Darker blue cards
            'border': (82, 121, 174),     # Light blue borders
            'lily_pad': (50, 180, 50)     # Green for lily pads
        }

    def get_species_color(self, species_id):
        """Get a consistent color for a given species ID."""
        if species_id not in self.species_colors:
            # Use the species_id as a seed to generate a consistent color
            random.seed(str(species_id))
            
            # Generate vibrant koi colors - traditional koi colors are white, red, orange, yellow, blue, and black
            # with various combinations
            
            # Traditional koi color palettes
            koi_palettes = [
                # White and red (Kohaku)
                [(220, 50, 50), (240, 100, 100)],
                
                # White, red and black (Showa)
                [(30, 30, 30), (200, 50, 50)],
                
                # White and black (Shiro Utsuri)
                [(40, 40, 40), (70, 70, 70)],
                
                # Solid orange/gold (Yamabuki Ogon)
                [(240, 180, 50), (250, 200, 80)],
                
                # Blue/gray (Asagi)
                [(80, 100, 180), (100, 130, 200)],
                
                # Metallic white/platinum (Platinum Ogon)
                [(220, 220, 220), (240, 240, 240)],
                
                # Red and white with blue (Sanke)
                [(220, 60, 60), (100, 120, 200)],
                
                # Calico (multicolor)
                [(240, 120, 50), (200, 80, 60)],
                
                # Copper/bronze
                [(180, 120, 60), (150, 100, 50)]
            ]
            
            # Choose one of the palettes based on species ID
            palette_index = hash(str(species_id)) % len(koi_palettes)
            palette = koi_palettes[palette_index]
            
            # Get a color from the palette
            color_index = hash(str(species_id) + "color") % len(palette)
            color = palette[color_index]
            
            # Add some variation within the palette
            # But keep the color in the same general hue family
            r = min(255, max(0, color[0] + random.randint(-20, 20)))
            g = min(255, max(0, color[1] + random.randint(-20, 20)))
            b = min(255, max(0, color[2] + random.randint(-20, 20)))
            
            self.species_colors[species_id] = (r, g, b)
        
        return self.species_colors[species_id]

    def render(self, koi, lily_pads):
        """Render the current state of the simulation."""
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
        
        # Fill the background with water color
        self.screen.fill(self.colors['water'])
        
        # Draw water ripple effects
        current_time = pygame.time.get_ticks() / 1000.0  # Time in seconds
        
        # Create circular ripples that expand over time
        num_ripples = 10
        for i in range(num_ripples):
            # Use consistent positions for ripples but have them appear at different times
            ripple_seed = i * 1000
            random.seed(ripple_seed)
            ripple_x = random.randint(0, self.scoreboard_rect.left)
            ripple_y = random.randint(0, self.scoreboard_rect.height)
            
            # Calculate ripple phase based on time
            phase = (current_time * 0.5 + i * 0.2) % 5  # 5 second cycle
            
            # Only show ripple during the first part of its cycle
            if phase < 2.5:
                # Radius grows with time
                radius = 20 + phase * 30
                # Fade out as the ripple expands
                alpha = max(0, int(150 * (1 - phase/2.5)))
                
                # Create a surface with per-pixel alpha for the ripple
                ripple_surface = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
                
                # Draw concentric circles for the ripple
                for j in range(3):
                    ripple_color = (*self.colors['ripple'], max(0, alpha - j*40))
                    # Draw only the outline
                    pygame.draw.circle(
                        ripple_surface, 
                        ripple_color, 
                        (radius, radius), 
                        radius - j*5, 
                        1
                    )
                
                # Blit the ripple onto the main screen
                self.screen.blit(
                    ripple_surface, 
                    (ripple_x - radius, ripple_y - radius)
                )
        
        # Add subtle light reflections on the water
        num_reflections = 15
        for i in range(num_reflections):
            random.seed(i * 2000)  # Consistent placement
            refl_x = random.randint(0, self.scoreboard_rect.left)
            refl_y = random.randint(0, self.scoreboard_rect.height)
            
            # Pulsating reflection based on time
            reflection_intensity = (math.sin(current_time * 1.5 + i * 0.7) + 1) * 0.5  # 0 to 1
            reflection_size = 8 + reflection_intensity * 10
            reflection_alpha = int(100 * reflection_intensity)
            
            # Create a surface for the reflection
            light_surface = pygame.Surface((reflection_size*2, reflection_size), pygame.SRCALPHA)
            
            # Draw an elliptical highlight
            reflection_color = (255, 255, 255, reflection_alpha)
            pygame.draw.ellipse(light_surface, reflection_color, (0, 0, reflection_size*2, reflection_size))
            
            # Blit the reflection onto the main screen
            self.screen.blit(
                light_surface, 
                (refl_x - reflection_size, refl_y - reflection_size/2)
            )
        
        # Draw lily pads
        for lily_pad in lily_pads:
            # Make sure the position is valid
            if lily_pad.position is None:
                continue
                
            # Draw a green circle for each lily pad
            pad_radius = 15
            
            # Create a more realistic lily pad with gradient and texture
            lily_surface = pygame.Surface((pad_radius*2, pad_radius*2), pygame.SRCALPHA)
            
            # Base lily pad shape (dark green)
            base_color = (40, 120, 40)
            pygame.draw.circle(lily_surface, base_color, (pad_radius, pad_radius), pad_radius)
            
            # Add a lighter center
            lighter_green = (70, 160, 70)
            pygame.draw.circle(lily_surface, lighter_green, (pad_radius, pad_radius), pad_radius * 0.7)
            
            # Add radial lines for texture
            line_color = (30, 100, 30, 200)  # Slightly transparent
            num_lines = 8
            for i in range(num_lines):
                angle = 2 * math.pi * i / num_lines
                line_end_x = pad_radius + math.cos(angle) * pad_radius * 0.9
                line_end_y = pad_radius + math.sin(angle) * pad_radius * 0.9
                pygame.draw.line(
                    lily_surface,
                    line_color,
                    (pad_radius, pad_radius),
                    (line_end_x, line_end_y),
                    1
                )
            
            # Draw a small shadow beneath the lily pad
            shadow_surface = pygame.Surface((pad_radius*2, pad_radius*2), pygame.SRCALPHA)
            shadow_color = (0, 0, 0, 50)  # Semi-transparent black
            pygame.draw.circle(shadow_surface, shadow_color, (pad_radius, pad_radius), pad_radius)
            
            # Add position jitter based on time to simulate floating movement
            jitter_x = math.sin(current_time + hash(str(lily_pad.position)) % 1000) * 1.0
            jitter_y = math.cos(current_time * 0.7 + hash(str(lily_pad.position)) % 1000) * 1.0
            
            # Blit the shadow with a slight offset
            self.screen.blit(
                shadow_surface, 
                (lily_pad.position[0] - pad_radius + 2, lily_pad.position[1] - pad_radius + 2)
            )
            
            # Blit the lily pad with slight movement
            self.screen.blit(
                lily_surface, 
                (lily_pad.position[0] - pad_radius + jitter_x, lily_pad.position[1] - pad_radius + jitter_y)
            )
        
        # Draw koi fish
        for fish in koi:
            # Skip if position is None or if the koi is not moving
            if fish.position is None or fish.last_position is None:
                continue
                
            # Get species color
            species_id = fish.species_id if hasattr(fish, 'species_id') else 0
            color = self.get_species_color(species_id)
            
            # Draw the koi fish
            size = fish.get_radius() if hasattr(fish, 'get_radius') else 10
            is_predator = fish.species_id == 999 if hasattr(fish, 'species_id') else False
            
            # Calculate velocity vector if both current and last positions are available
            velocity = None
            if fish.position and fish.last_position:
                velocity = (fish.position[0] - fish.last_position[0], 
                           fish.position[1] - fish.last_position[1])
            
            self.draw_koi_fish(self.screen, fish.position, color, size, is_predator, velocity)
        
        # Draw the scoreboard
        self._render_scoreboard()
        
        # Update the display
        pygame.display.flip()
        
        # Limit the frame rate
        self.clock.tick(30)
        
        return True

    def set_generation(self, generation):
        """Set the current generation number for display."""
        self.generation = generation
    
    def _rotate_point(self, point, origin, angle_rad):
        """Rotate a point around an origin by the given angle in radians."""
        tx, ty = point[0] - origin[0], point[1] - origin[1]
        rx = tx * math.cos(angle_rad) - ty * math.sin(angle_rad)
        ry = tx * math.sin(angle_rad) + ty * math.cos(angle_rad)
        return (rx + origin[0], ry + origin[1])
        
    def draw_koi_fish_detail(self, screen, position, color, base_radius, num_fins=5, num_nodes=10, is_predator=False):
        """Draw a detailed koi fish with fins."""
        # Calculate dynamic radius based on node count
        radius = max(5, min(20, base_radius * (1 + num_nodes * 0.05)))
        
        # Calculate body dimensions - koi have elongated bodies
        body_length = radius * 3  # More elongated
        body_width = radius * 1.6
        
        # Get color components
        r, g, b = color
        
        # Calculate orientation - fish should face to the right by default
        orientation = 0  # Default orientation (facing right)
        
        # Draw main body - more tapered toward the tail
        body_points = []
        num_body_points = 12
        for i in range(num_body_points):
            # Calculate proportional distance along body (0 to 1)
            t = i / (num_body_points - 1)
            
            # Taper width as we move toward tail
            width_factor = 1 - 0.5 * (t ** 2) 
            
            # X coordinate goes from +body_length/2 to -body_length/2
            x = position[0] + body_length/2 - t * body_length
            
            # Top and bottom points
            if i == 0:
                # Head is slightly rounded
                top_y = position[1] - body_width/2 * width_factor * 0.8
                bottom_y = position[1] + body_width/2 * width_factor * 0.8
            else:
                top_y = position[1] - body_width/2 * width_factor
                bottom_y = position[1] + body_width/2 * width_factor
            
            body_points.append((x, top_y))
            # Insert the bottom points in reverse order later
            if i == num_body_points - 1:
                body_points.append((x, bottom_y))
        
        # Add bottom points in reverse
        for i in range(num_body_points - 2, -1, -1):
            t = i / (num_body_points - 1)
            width_factor = 1 - 0.5 * (t ** 2)
            x = position[0] + body_length/2 - t * body_length
            bottom_y = position[1] + body_width/2 * width_factor
            if i == 0:
                bottom_y = position[1] + body_width/2 * width_factor * 0.8
            body_points.append((x, bottom_y))
        
        # Draw the main body (custom polygon)
        pygame.draw.polygon(screen, color, body_points)
        
        # Generate a pattern based on the species (using hash of color)
        pattern_type = (r + g + b) % 4  # 0: solid, 1: two-tone, 2: spotted, 3: striped
        
        # Create a secondary color by adjusting the primary color
        # More saturated for better contrast
        secondary_color = (
            min(255, r + 60) if r < 128 else max(0, r - 60),
            min(255, g + 60) if g < 128 else max(0, g - 60),
            min(255, b + 60) if b < 128 else max(0, b - 60)
        )
        
        # Add white as an accent color for traditional koi patterns
        white = (255, 255, 255)
        
        # Create pattern based on type
        if pattern_type == 1:  # Two-tone (like Kohaku koi)
            # Draw white on the top half
            pattern_points = []
            for i in range(num_body_points):
                t = i / (num_body_points - 1)
                width_factor = 1 - 0.5 * (t ** 2)
                x = position[0] + body_length/2 - t * body_length
                y = position[1] - body_width/4 * width_factor
                pattern_points.append((x, y))
            
            # Add center line
            for i in range(num_body_points - 1, -1, -1):
                t = i / (num_body_points - 1)
                width_factor = 1 - 0.5 * (t ** 2)
                x = position[0] + body_length/2 - t * body_length
                pattern_points.append((x, position[1]))
            
            pygame.draw.polygon(screen, white, pattern_points)
            
        elif pattern_type == 2:  # Spotted (like Bekko koi)
            # Add spots
            num_spots = random.randint(3, 6)
            for _ in range(num_spots):
                # Random position within the body
                spot_t = random.uniform(0.1, 0.9)
                width_factor = 1 - 0.5 * (spot_t ** 2)
                spot_x = position[0] + body_length/2 - spot_t * body_length
                spot_y = position[1] + random.uniform(-0.7, 0.7) * body_width/2 * width_factor
                spot_radius = random.uniform(0.1, 0.25) * radius
                
                pygame.draw.circle(screen, secondary_color, (spot_x, spot_y), spot_radius)
                
        elif pattern_type == 3:  # Striped (like Showa koi)
            # Add diagonal stripes
            num_stripes = random.randint(3, 5)
            for i in range(num_stripes):
                stripe_t = 0.2 + (i * 0.6 / num_stripes)
                width_factor = 1 - 0.5 * (stripe_t ** 2)
                stripe_x = position[0] + body_length/2 - stripe_t * body_length
                
                # Alternate stripe colors
                stripe_color = white if i % 2 == 0 else secondary_color
                
                # Draw diagonal stripe
                stripe_width = radius * 0.3
                pygame.draw.line(
                    screen, 
                    stripe_color,
                    (stripe_x - stripe_width/2, position[1] - body_width/2 * width_factor),
                    (stripe_x + stripe_width/2, position[1] + body_width/2 * width_factor),
                    int(radius * 0.4)
                )
        
        # Add a lighter belly for all types
        belly_color = (
            min(255, r + 40),
            min(255, g + 40),
            min(255, b + 40)
        )
        
        belly_points = []
        for i in range(num_body_points):
            t = i / (num_body_points - 1)
            width_factor = 1 - 0.5 * (t ** 2)
            x = position[0] + body_length/2 - t * body_length
            y = position[1]  # Center line
            belly_points.append((x, y))
            
            if i != num_body_points - 1:  # Skip the tail point
                bottom_y = position[1] + body_width/2 * width_factor
                if i == 0:
                    bottom_y = position[1] + body_width/2 * width_factor * 0.8
                belly_points.append((x, bottom_y))
        
        pygame.draw.polygon(screen, belly_color, belly_points, 0)
        
        # Add dorsal fin at the top
        dorsal_start_x = position[0] + body_length/4
        dorsal_start_y = position[1] - body_width/2 * 0.8
        dorsal_mid_x = position[0]
        dorsal_mid_y = position[1] - body_width/2 * 1.4
        dorsal_end_x = position[0] - body_length/4
        dorsal_end_y = position[1] - body_width/2 * 0.75
        
        pygame.draw.polygon(
            screen, 
            color, 
            [(dorsal_start_x, dorsal_start_y), 
             (dorsal_mid_x, dorsal_mid_y), 
             (dorsal_end_x, dorsal_end_y)]
        )
        
        # Add pectoral fin on the side
        pectoral_start_x = position[0] + body_length/4
        pectoral_start_y = position[1] + body_width/4
        pectoral_mid_x = position[0] + body_length/3
        pectoral_mid_y = position[1] + body_width/2 * 1.2
        pectoral_end_x = position[0]
        pectoral_end_y = position[1] + body_width/4
        
        pygame.draw.polygon(
            screen, 
            color, 
            [(pectoral_start_x, pectoral_start_y), 
             (pectoral_mid_x, pectoral_mid_y), 
             (pectoral_end_x, pectoral_end_y)]
        )
        
        # Add a more elegant tail
        tail_start_x = position[0] - body_length/2
        tail_start_y = position[1]
        
        # Top tail fin
        tail_top_mid_x = position[0] - body_length/2 - radius * 0.8
        tail_top_mid_y = position[1] - radius * 0.5
        tail_top_end_x = position[0] - body_length/2 - radius * 1.2
        tail_top_end_y = position[1] - radius * 1.0
        
        # Bottom tail fin
        tail_bottom_mid_x = position[0] - body_length/2 - radius * 0.8
        tail_bottom_mid_y = position[1] + radius * 0.5
        tail_bottom_end_x = position[0] - body_length/2 - radius * 1.2
        tail_bottom_end_y = position[1] + radius * 1.0
        
        # Draw top part of tail
        pygame.draw.polygon(
            screen,
            color,
            [(tail_start_x, tail_start_y - radius * 0.2),
             (tail_top_mid_x, tail_top_mid_y),
             (tail_top_end_x, tail_top_end_y)]
        )
        
        # Draw bottom part of tail
        pygame.draw.polygon(
            screen,
            color,
            [(tail_start_x, tail_start_y + radius * 0.2),
             (tail_bottom_mid_x, tail_bottom_mid_y),
             (tail_bottom_end_x, tail_bottom_end_y)]
        )
        
        # Add stripes to the tail
        tail_stripe_color = secondary_color
        pygame.draw.line(
            screen,
            tail_stripe_color,
            (tail_top_mid_x, tail_top_mid_y),
            (tail_top_end_x, tail_top_end_y),
            int(radius * 0.15)
        )
        
        pygame.draw.line(
            screen,
            tail_stripe_color,
            (tail_bottom_mid_x, tail_bottom_mid_y),
            (tail_bottom_end_x, tail_bottom_end_y),
            int(radius * 0.15)
        )
        
        # Add eye
        eye_pos = (position[0] + body_length/2 - radius * 0.3, position[1] - radius * 0.2)
        pygame.draw.circle(screen, (255, 255, 255), eye_pos, radius * 0.25)
        pygame.draw.circle(screen, (0, 0, 0), eye_pos, radius * 0.12)
        
        # Add highlight to eye
        highlight_pos = (eye_pos[0] - radius * 0.05, eye_pos[1] - radius * 0.05)
        pygame.draw.circle(screen, (255, 255, 255), highlight_pos, radius * 0.06)
        
        # Add gill marking
        gill_x_offset = body_length/2 - radius * 0.8
        rad_angle = math.radians(orientation)  # Using angle, not orientation in draw_koi_fish
        gill_center_rotated = self._rotate_point((gill_x_offset, 0), (0, 0), rad_angle)
        gill_center = (gill_center_rotated[0] + position[0], gill_center_rotated[1] + position[1])
        
        # Calculate gill arc angles based on fish rotation
        gill_start_angle = rad_angle + math.pi * 0.2
        gill_end_angle = rad_angle + math.pi * 0.8
        
        # Ensure gill_rect has integer coordinates and positive width/height
        gill_rect = pygame.Rect(
            int(gill_center[0] - radius * 0.5),
            int(gill_center[1] - radius * 0.8),
            max(1, int(radius)),
            max(1, int(radius * 1.6))
        )
        
        try:
            # Ensure valid RGB color values
            if isinstance(r, (int, float)) and isinstance(g, (int, float)) and isinstance(b, (int, float)):
                gill_color = (max(0, min(255, int(r - 30))), 
                             max(0, min(255, int(g - 30))), 
                             max(0, min(255, int(b - 30))))
                pygame.draw.arc(
                    screen,
                    gill_color,
                    gill_rect,
                    gill_start_angle,
                    gill_end_angle,
                    2
                )
            else:
                print(f"Warning: Invalid color component types: r={type(r)}, g={type(g)}, b={type(b)}")
        except ValueError as e:
            print(f"Error drawing gill arc: {e}")
            print(f"Color values: r={r}, g={g}, b={b}")
            print(f"Gill rect: {gill_rect}")
        
        # Add predator features
        if is_predator:
            # Enhanced gill markings
            try:
                # Ensure valid RGB color values
                if isinstance(r, (int, float)) and isinstance(g, (int, float)) and isinstance(b, (int, float)):
                    predator_gill_color = (max(0, min(255, int(r - 50))), 
                                         max(0, min(255, int(g - 50))), 
                                         max(0, min(255, int(b - 50))))
                    pygame.draw.arc(
                        screen,
                        predator_gill_color,
                        gill_rect,
                        gill_start_angle,
                        gill_end_angle,
                        3
                    )
                else:
                    print(f"Warning: Invalid predator color component types: r={type(r)}, g={type(g)}, b={type(b)}")
            except ValueError as e:
                print(f"Error drawing predator gill arc: {e}")
                print(f"Color values: r={r}, g={g}, b={b}")
                print(f"Gill rect: {gill_rect}")
            
            # Add teeth at mouth
            teeth_x_offset = body_length/2
            teeth_y_offset = radius * 0.2
            
            # Create triangle teeth points and rotate them
            teeth_points = [
                (teeth_x_offset, -teeth_y_offset),
                (teeth_x_offset + radius * 0.2, 0),
                (teeth_x_offset, teeth_y_offset)
            ]
            
            rotated_teeth_points = []
            for point in teeth_points:
                rotated = self._rotate_point(point, (0, 0), rad_angle)
                rotated_teeth_points.append((rotated[0] + position[0], rotated[1] + position[1]))
            
            pygame.draw.polygon(screen, (255, 255, 255), rotated_teeth_points)

    def _render_scoreboard(self):
        """Render the scoreboard showing top species."""
        # Fill scoreboard background
        pygame.draw.rect(self.screen, self.colors['card'], self.scoreboard_rect)
        
        # Draw title
        title = self.title_font.render("Koi Pond Simulation", True, self.colors['title'])
        title_rect = title.get_rect(centerx=self.scoreboard_rect.centerx, top=self.scoreboard_rect.top + 20)
        self.screen.blit(title, title_rect)
        
        # Draw generation counter
        gen_text = self.header_font.render(f"Generation: {self.generation}", True, self.colors['title'])
        gen_rect = gen_text.get_rect(centerx=self.scoreboard_rect.centerx, top=title_rect.bottom + 20)
        self.screen.blit(gen_text, gen_rect)
        
        # Get top species from scoreboard
        from scoreboard import Scoreboard
        top_species = Scoreboard.get_top_species(5)
        
        # Draw species cards
        y_offset = gen_rect.bottom + 30
        card_height = 100
        card_width = self.scoreboard_rect.width - 40
        
        for i, (species_id, record) in enumerate(top_species):
            # Draw card background
            card_rect = pygame.Rect(
                self.scoreboard_rect.left + 20,
                y_offset,
                card_width,
                card_height
            )
            pygame.draw.rect(self.screen, self.colors['card'], card_rect)
            pygame.draw.rect(self.screen, self.colors['border'], card_rect, 2)
            
            # Draw rank
            rank_text = self.header_font.render(f"#{i+1}", True, self.colors['highlight'])
            self.screen.blit(rank_text, (card_rect.x + 10, card_rect.y + 10))
            
            # Draw koi icon
            rank_pos = (card_rect.x + 25, card_rect.y + 50)
            color = self.get_species_color(species_id)
            size = record.get('size', 20)
            
            # Draw the koi with its actual properties
            self.draw_koi_fish_detail(
                self.screen,
                rank_pos,
                color,
                size / 2,  # Convert diameter to radius
                num_fins=5,
                num_nodes=10,
                is_predator=False
            )
            
            # Species name with custom color based on rank
            name = record['scientific_name'] or f'Species {species_id}'
            name_color = self.get_species_color(species_id)
            name_text = self.font.render(name, True, name_color)
            self.screen.blit(name_text, (card_rect.x + 50, card_rect.y + 15))
            
            # Fitness score
            fitness_text = self.font.render(
                f"Fitness: {int(record['highest_fitness']):,}", 
                True, 
                self.colors['text']
            )
            self.screen.blit(fitness_text, (card_rect.x + 50, card_rect.y + 40))
            
            # Generation range
            gen_text = self.font.render(
                f"Gen {record['first_generation']} → {record['last_generation']}", 
                True, 
                self.colors['text']
            )
            self.screen.blit(gen_text, (card_rect.x + 50, card_rect.y + 65))
            
            y_offset += card_height + 10

    def draw_koi_fish(self, screen, position, color, size, is_predator, velocity=None):
        x, y = position
        
        # Calculate rotation angle based on velocity
        angle = 0
        if velocity is not None:
            velocity_x, velocity_y = velocity
            if velocity_x != 0 or velocity_y != 0:  # Only calculate angle if moving
                angle = math.degrees(math.atan2(velocity_y, velocity_x))
        
        # Draw vision cone
        vision_length = 80  # Length of vision cone
        vision_angle = 120  # Total angle of vision cone
        
        # Draw dotted arc for vision range
        radius = vision_length
        start_angle = math.radians(angle - vision_angle/2)
        end_angle = math.radians(angle + vision_angle/2)
        
        # Draw dotted arc line
        points = []
        num_dots = 20
        for i in range(num_dots):
            current_angle = start_angle + (end_angle - start_angle) * i / (num_dots - 1)
            dot_x = x + radius * math.cos(current_angle)
            dot_y = y + radius * math.sin(current_angle)
            points.append((int(dot_x), int(dot_y)))
        
        # Draw dots with slight transparency
        vision_color = (*color, 100)
        for point in points:
            pygame.draw.circle(screen, vision_color, point, 1)
        
        # Draw lines to first and last dots
        pygame.draw.line(screen, vision_color, (x, y), points[0], 1)
        pygame.draw.line(screen, vision_color, (x, y), points[-1], 1)
        
        # Get color components
        r, g, b = color
        
        # Adjust size for consistency with the enhanced koi fish drawing
        base_radius = size * 0.8
        
        # Calculate body dimensions
        body_length = base_radius * 3
        body_width = base_radius * 1.6
        
        # Create transformation matrix for rotation
        rad_angle = math.radians(angle)
        rotation_matrix = [
            [math.cos(rad_angle), -math.sin(rad_angle)],
            [math.sin(rad_angle), math.cos(rad_angle)]
        ]
        
        # Draw main body - using polygon approach for better shape
        body_points = []
        num_body_points = 12
        
        # Build body points without rotation first
        unrotated_body_points = []
        
        for i in range(num_body_points):
            # Calculate proportional distance along body (0 to 1)
            t = i / (num_body_points - 1)
            
            # Taper width as we move toward tail
            width_factor = 1 - 0.5 * (t ** 2)
            
            # X coordinate goes from +body_length/2 to -body_length/2
            # Center at (0,0) for easier rotation
            point_x = body_length/2 - t * body_length
            
            # Top and bottom points
            if i == 0:
                # Head is slightly rounded
                top_y = -body_width/2 * width_factor * 0.8
            else:
                top_y = -body_width/2 * width_factor
            
            unrotated_body_points.append((point_x, top_y))
            
            # Add tail endpoint for bottom curve
            if i == num_body_points - 1:
                unrotated_body_points.append((point_x, 0))
        
        # Add bottom points in reverse
        for i in range(num_body_points - 2, -1, -1):
            t = i / (num_body_points - 1)
            width_factor = 1 - 0.5 * (t ** 2)
            point_x = body_length/2 - t * body_length
            
            if i == 0:
                bottom_y = body_width/2 * width_factor * 0.8
            else:
                bottom_y = body_width/2 * width_factor
                
            unrotated_body_points.append((point_x, bottom_y))
        
        # Rotate and translate all body points
        for point in unrotated_body_points:
            rotated_point = self._rotate_point(point, (0, 0), rad_angle)
            body_points.append((rotated_point[0] + x, rotated_point[1] + y))
        
        # Draw the main body
        pygame.draw.polygon(screen, color, body_points)
        
        # Generate a pattern based on species (using hash of color)
        pattern_type = (r + g + b) % 4  # 0: solid, 1: two-tone, 2: spotted, 3: striped
        
        # Create secondary color
        secondary_color = (
            min(255, r + 60) if r < 128 else max(0, r - 60),
            min(255, g + 60) if g < 128 else max(0, g - 60),
            min(255, b + 60) if b < 128 else max(0, b - 60)
        )
        
        # White for traditional koi patterns
        white = (255, 255, 255)
        
        # Apply patterns based on rotation
        if pattern_type == 1:  # Two-tone (Kohaku)
            # Create points for two-tone pattern
            pattern_points = []
            
            # Top white pattern
            for i in range(num_body_points):
                t = i / (num_body_points - 1)
                width_factor = 1 - 0.5 * (t ** 2)
                point_x = body_length/2 - t * body_length
                point_y = -body_width/4 * width_factor
                
                # Rotate and translate
                rotated = self._rotate_point((point_x, point_y), (0, 0), rad_angle)
                pattern_points.append((rotated[0] + x, rotated[1] + y))
            
            # Add center line
            for i in range(num_body_points - 1, -1, -1):
                t = i / (num_body_points - 1)
                point_x = body_length/2 - t * body_length
                
                # Rotate and translate
                rotated = self._rotate_point((point_x, 0), (0, 0), rad_angle)
                pattern_points.append((rotated[0] + x, rotated[1] + y))
            
            pygame.draw.polygon(screen, white, pattern_points)
            
        elif pattern_type == 2:  # Spotted (Bekko)
            # Add spots
            num_spots = random.randint(3, 6)
            for _ in range(num_spots):
                # Random position within body
                spot_t = random.uniform(0.1, 0.9)
                width_factor = 1 - 0.5 * (spot_t ** 2)
                spot_x = body_length/2 - spot_t * body_length
                spot_y = random.uniform(-0.7, 0.7) * body_width/2 * width_factor
                
                # Rotate and translate
                rotated = self._rotate_point((spot_x, spot_y), (0, 0), rad_angle)
                spot_pos = (rotated[0] + x, rotated[1] + y)
                spot_radius = random.uniform(0.1, 0.25) * base_radius
                
                pygame.draw.circle(screen, secondary_color, spot_pos, spot_radius)
                
        elif pattern_type == 3:  # Striped (Showa)
            # Add diagonal stripes
            num_stripes = random.randint(3, 5)
            for i in range(num_stripes):
                stripe_t = 0.2 + (i * 0.6 / num_stripes)
                width_factor = 1 - 0.5 * (stripe_t ** 2)
                stripe_x = body_length/2 - stripe_t * body_length
                
                # Start and end points for the stripe
                stripe_top = (stripe_x, -body_width/2 * width_factor)
                stripe_bottom = (stripe_x, body_width/2 * width_factor)
                
                # Rotate and translate
                rotated_top = self._rotate_point(stripe_top, (0, 0), rad_angle)
                rotated_bottom = self._rotate_point(stripe_bottom, (0, 0), rad_angle)
                
                # Alternate stripe colors
                stripe_color = white if i % 2 == 0 else secondary_color
                
                pygame.draw.line(
                    screen,
                    stripe_color,
                    (rotated_top[0] + x, rotated_top[1] + y),
                    (rotated_bottom[0] + x, rotated_bottom[1] + y),
                    int(base_radius * 0.4)
                )
        
        # Add lighter belly
        belly_color = (
            min(255, r + 40),
            min(255, g + 40),
            min(255, b + 40)
        )
        
        # Create belly points
        belly_points = []
        for i in range(num_body_points):
            t = i / (num_body_points - 1)
            width_factor = 1 - 0.5 * (t ** 2)
            point_x = body_length/2 - t * body_length
            
            # Center point
            center_rotated = self._rotate_point((point_x, 0), (0, 0), rad_angle)
            belly_points.append((center_rotated[0] + x, center_rotated[1] + y))
            
            # Only add bottom points, not at tail tip
            if i != num_body_points - 1:
                if i == 0:
                    bottom_y = body_width/2 * width_factor * 0.8
                else:
                    bottom_y = body_width/2 * width_factor
                    
                bottom_rotated = self._rotate_point((point_x, bottom_y), (0, 0), rad_angle)
                belly_points.append((bottom_rotated[0] + x, bottom_rotated[1] + y))
        
        pygame.draw.polygon(screen, belly_color, belly_points, 0)
        
        # Add fins
        # Dorsal fin
        dorsal_points = []
        dorsal_start = (body_length/4, -body_width/2 * 0.8)
        dorsal_mid = (0, -body_width/2 * 1.4)
        dorsal_end = (-body_length/4, -body_width/2 * 0.75)
        
        for point in [dorsal_start, dorsal_mid, dorsal_end]:
            rotated = self._rotate_point(point, (0, 0), rad_angle)
            dorsal_points.append((rotated[0] + x, rotated[1] + y))
        
        pygame.draw.polygon(screen, color, dorsal_points)
        
        # Pectoral fin
        pectoral_points = []
        pectoral_start = (body_length/4, body_width/4)
        pectoral_mid = (body_length/3, body_width/2 * 1.2)
        pectoral_end = (0, body_width/4)
        
        for point in [pectoral_start, pectoral_mid, pectoral_end]:
            rotated = self._rotate_point(point, (0, 0), rad_angle)
            pectoral_points.append((rotated[0] + x, rotated[1] + y))
        
        pygame.draw.polygon(screen, color, pectoral_points)
        
        # Tail fins
        # Top tail fin
        tail_top_points = []
        tail_start = (-body_length/2, -base_radius * 0.2)
        tail_top_mid = (-body_length/2 - base_radius * 0.8, -base_radius * 0.5)
        tail_top_end = (-body_length/2 - base_radius * 1.2, -base_radius * 1.0)
        
        for point in [tail_start, tail_top_mid, tail_top_end]:
            rotated = self._rotate_point(point, (0, 0), rad_angle)
            tail_top_points.append((rotated[0] + x, rotated[1] + y))
        
        pygame.draw.polygon(screen, color, tail_top_points)
        
        # Bottom tail fin
        tail_bottom_points = []
        tail_start = (-body_length/2, base_radius * 0.2)
        tail_bottom_mid = (-body_length/2 - base_radius * 0.8, base_radius * 0.5)
        tail_bottom_end = (-body_length/2 - base_radius * 1.2, base_radius * 1.0)
        
        for point in [tail_start, tail_bottom_mid, tail_bottom_end]:
            rotated = self._rotate_point(point, (0, 0), rad_angle)
            tail_bottom_points.append((rotated[0] + x, rotated[1] + y))
        
        pygame.draw.polygon(screen, color, tail_bottom_points)
        
        # Add stripes to tail
        top_mid_rotated = self._rotate_point(tail_top_mid, (0, 0), rad_angle)
        top_end_rotated = self._rotate_point(tail_top_end, (0, 0), rad_angle)
        bottom_mid_rotated = self._rotate_point(tail_bottom_mid, (0, 0), rad_angle)
        bottom_end_rotated = self._rotate_point(tail_bottom_end, (0, 0), rad_angle)
        
        pygame.draw.line(
            screen,
            secondary_color,
            (top_mid_rotated[0] + x, top_mid_rotated[1] + y),
            (top_end_rotated[0] + x, top_end_rotated[1] + y),
            int(base_radius * 0.15)
        )
        
        pygame.draw.line(
            screen,
            secondary_color,
            (bottom_mid_rotated[0] + x, bottom_mid_rotated[1] + y),
            (bottom_end_rotated[0] + x, bottom_end_rotated[1] + y),
            int(base_radius * 0.15)
        )
        
        # Add eye
        eye_x_offset = body_length/2 - base_radius * 0.3
        eye_y_offset = -base_radius * 0.2
        eye_rotated = self._rotate_point((eye_x_offset, eye_y_offset), (0, 0), rad_angle)
        eye_pos = (eye_rotated[0] + x, eye_rotated[1] + y)
        
        pygame.draw.circle(screen, (255, 255, 255), eye_pos, base_radius * 0.25)
        pygame.draw.circle(screen, (0, 0, 0), eye_pos, base_radius * 0.12)
        
        # Add highlight to eye
        highlight_offset = (-base_radius * 0.05, -base_radius * 0.05)
        highlight_rotated = self._rotate_point(
            (eye_x_offset + highlight_offset[0], eye_y_offset + highlight_offset[1]), 
            (0, 0), 
            rad_angle
        )
        highlight_pos = (highlight_rotated[0] + x, highlight_rotated[1] + y)
        pygame.draw.circle(screen, (255, 255, 255), highlight_pos, base_radius * 0.06)
        
        # Add gill marking
        gill_x_offset = body_length/2 - base_radius * 0.8
        rad_angle = math.radians(angle)  # Using angle, not orientation in draw_koi_fish
        gill_center_rotated = self._rotate_point((gill_x_offset, 0), (0, 0), rad_angle)
        gill_center = (gill_center_rotated[0] + x, gill_center_rotated[1] + y)
        
        # Calculate gill arc angles based on fish rotation
        gill_start_angle = rad_angle + math.pi * 0.2
        gill_end_angle = rad_angle + math.pi * 0.8
        
        # Ensure gill_rect has integer coordinates and positive width/height
        gill_rect = pygame.Rect(
            int(gill_center[0] - base_radius * 0.5),
            int(gill_center[1] - base_radius * 0.8),
            max(1, int(base_radius)),
            max(1, int(base_radius * 1.6))
        )
        
        try:
            # Ensure valid RGB color values
            if isinstance(r, (int, float)) and isinstance(g, (int, float)) and isinstance(b, (int, float)):
                gill_color = (max(0, min(255, int(r - 30))), 
                             max(0, min(255, int(g - 30))), 
                             max(0, min(255, int(b - 30))))
                pygame.draw.arc(
                    screen,
                    gill_color,
                    gill_rect,
                    gill_start_angle,
                    gill_end_angle,
                    2
                )
            else:
                print(f"Warning: Invalid color component types: r={type(r)}, g={type(g)}, b={type(b)}")
        except ValueError as e:
            print(f"Error drawing gill arc: {e}")
            print(f"Color values: r={r}, g={g}, b={b}")
            print(f"Gill rect: {gill_rect}")
        
        # Add predator features
        if is_predator:
            # Enhanced gill markings
            try:
                # Ensure valid RGB color values
                if isinstance(r, (int, float)) and isinstance(g, (int, float)) and isinstance(b, (int, float)):
                    predator_gill_color = (max(0, min(255, int(r - 50))), 
                                         max(0, min(255, int(g - 50))), 
                                         max(0, min(255, int(b - 50))))
                    pygame.draw.arc(
                        screen,
                        predator_gill_color,
                        gill_rect,
                        gill_start_angle,
                        gill_end_angle,
                        3
                    )
                else:
                    print(f"Warning: Invalid predator color component types: r={type(r)}, g={type(g)}, b={type(b)}")
            except ValueError as e:
                print(f"Error drawing predator gill arc: {e}")
                print(f"Color values: r={r}, g={g}, b={b}")
                print(f"Gill rect: {gill_rect}")
            
            # Add teeth at mouth
            teeth_x_offset = body_length/2
            teeth_y_offset = base_radius * 0.2
            
            # Create triangle teeth points and rotate them
            teeth_points = [
                (teeth_x_offset, -teeth_y_offset),
                (teeth_x_offset + base_radius * 0.2, 0),
                (teeth_x_offset, teeth_y_offset)
            ]
            
            rotated_teeth_points = []
            for point in teeth_points:
                rotated = self._rotate_point(point, (0, 0), rad_angle)
                rotated_teeth_points.append((rotated[0] + x, rotated[1] + y))
            
            pygame.draw.polygon(screen, (255, 255, 255), rotated_teeth_points)
