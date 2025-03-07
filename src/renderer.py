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
            'lily_pad': (50, 180, 50),    # Green for lily pads
            'bg_darker': (50, 70, 100),   # Darker background for scoreboard
        }

        # Toggle for showing koi field of vision
        self.show_vision = True

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
            elif event.type == pygame.KEYDOWN:
                # Handle key press events
                if event.key == pygame.K_v:
                    # Toggle vision cone display when V is pressed
                    self.show_vision = not self.show_vision
                    print(f"Vision display: {'ON' if self.show_vision else 'OFF'}")
        
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
            
            # Use the koi's orientation and body flex for natural movement
            orientation = fish.orientation if hasattr(fish, 'orientation') else None
            body_flex = fish.body_flex if hasattr(fish, 'body_flex') else 0
            
            # If no orientation is stored, calculate from velocity as fallback
            if orientation is None and fish.position and fish.last_position:
                velocity = (fish.position[0] - fish.last_position[0], 
                           fish.position[1] - fish.last_position[1])
                if velocity[0] != 0 or velocity[1] != 0:
                    orientation = math.degrees(math.atan2(velocity[1], velocity[0]))
                else:
                    orientation = 0
            
            self.draw_koi_fish(self.screen, fish.position, color, size, is_predator, orientation, body_flex)
        
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
        
        # Update the scoreboard's generation counter as well
        from scoreboard import Scoreboard
        if generation > Scoreboard.get_current_generation():
            Scoreboard.set_current_generation(generation)
    
    def _rotate_point(self, point, origin, angle_rad):
        """Rotate a point around an origin by the given angle in radians."""
        tx, ty = point[0] - origin[0], point[1] - origin[1]
        rx = tx * math.cos(angle_rad) - ty * math.sin(angle_rad)
        ry = tx * math.sin(angle_rad) + ty * math.cos(angle_rad)
        return (rx + origin[0], ry + origin[1])
        
    def draw_koi_fish_detail(self, screen, position, color, base_radius, num_fins=5, num_nodes=10, is_predator=False, body_flex=0):
        """Draw a detailed koi fish with fins."""
        # Calculate dynamic radius based on node count
        radius = max(5, min(20, base_radius * (1 + num_nodes * 0.05)))
        
        # Calculate body dimensions - koi have elongated bodies
        body_length = radius * 3  # More elongated
        body_width = radius * 1.8  # Wider for top-down view
        
        # Get color components
        r, g, b = color
        
        # Calculate orientation - fish should face to the right by default
        orientation = 0  # Default orientation (facing right)
        
        # Draw main body - oval shape for top-down view
        body_points = []
        num_body_points = 16  # More points for smoother oval
        
        # Create points for the oval body shape
        for i in range(num_body_points):
            angle_around = 2 * math.pi * i / num_body_points
            
            # Calculate distance from center based on angle
            # Create oval shape that's longer than it is wide
            t = abs(math.sin(angle_around))  # 0 at sides, 1 at front/back
            
            # Taper the back (tail) end
            if angle_around > math.pi / 2 and angle_around < 3 * math.pi / 2:
                # This is the back half
                taper_factor = 0.7  # Reduce width at tail
            else:
                # This is the front half
                taper_factor = 1.0  # Full width at head
            
            # Apply body flex to create a natural swimming motion
            flex_amount = 0
            is_tail_half = (angle_around > math.pi / 2 and angle_around < 3 * math.pi / 2)
            if is_tail_half:
                # Normalize position along tail 
                tail_pos = (angle_around - math.pi / 2) / math.pi
                # Apply sinusoidal curve for natural bend
                flex_amount = body_flex * tail_pos * body_width * 0.3
            
            # Calculate point position
            x = position[0] + math.cos(angle_around) * body_length/2 * taper_factor
            y = position[1] + math.sin(angle_around) * body_width/2
            
            # Apply flex to position
            if is_tail_half:
                y += flex_amount
                
            body_points.append((x, y))
        
        # Draw the main body
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
            # Create points for center pattern
            pattern_width = body_width * 0.4  # Make pattern narrower
            pattern_points = []
            
            # Create an inner pattern shape
            for i in range(num_body_points):
                angle_around = 2 * math.pi * i / num_body_points
                
                # Calculate distance from center
                if angle_around > math.pi / 2 and angle_around < 3 * math.pi / 2:
                    # This is the back half
                    taper_factor = 0.6
                else:
                    # This is the front half
                    taper_factor = 0.9
                
                # Calculate the point's position - smaller than the body
                x = position[0] + math.cos(angle_around) * body_length/2 * taper_factor * 0.7
                y = position[1] + math.sin(angle_around) * pattern_width/2
                
                # Apply flex to pattern
                if angle_around > math.pi / 2 and angle_around < 3 * math.pi / 2:
                    tail_pos = (angle_around - math.pi / 2) / math.pi
                    flex_amount = body_flex * tail_pos * pattern_width * 0.3
                    y += flex_amount
                
                pattern_points.append((x, y))
            
            # Draw the pattern
            pygame.draw.polygon(screen, white, pattern_points)
            
        elif pattern_type == 2:  # Spotted (like Bekko koi)
            # Add spots scattered across the body
            num_spots = random.randint(3, 5)
            for _ in range(num_spots):
                # Random position within the oval body
                spot_angle = random.uniform(0, 2 * math.pi)
                spot_dist = random.uniform(0.2, 0.7) * body_length/2
                
                # Calculate position
                if spot_angle > math.pi / 2 and spot_angle < 3 * math.pi / 2:
                    spot_dist *= 0.7  # Smaller spots near tail
                
                # Calculate spot position
                spot_x = position[0] + math.cos(spot_angle) * spot_dist
                spot_y = position[1] + math.sin(spot_angle) * spot_dist * (body_width/body_length)
                
                # Apply flex to spots in tail area
                if spot_angle > math.pi / 2 and spot_angle < 3 * math.pi / 2:
                    tail_pos = (spot_angle - math.pi / 2) / math.pi
                    flex_amount = body_flex * tail_pos * body_width * 0.3
                    spot_y += flex_amount
                
                # Random spot size but smaller for scoreboard
                spot_radius = random.uniform(0.15, 0.25) * radius
                
                # Draw the spot
                pygame.draw.circle(screen, secondary_color, (spot_x, spot_y), spot_radius)
                
        elif pattern_type == 3:  # Striped (like Showa koi)
            # Add stripes across the body
            num_stripes = random.randint(2, 4)
            for i in range(num_stripes):
                # Position stripe at intervals along body
                stripe_pos = 0.2 + (i * 0.6 / num_stripes)
                
                # Calculate stripe points
                stripe_points = []
                for angle_offset in [-0.3, 0.3]:  # Slightly angled stripes
                    # Calculate position
                    stripe_x = position[0] + (body_length/2 - stripe_pos * body_length)
                    stripe_y = position[1] + body_width/2 * angle_offset
                    
                    # Apply flex if in tail area
                    if stripe_pos > 0.5:  # If in tail half
                        tail_pos = (stripe_pos - 0.5) * 2
                        flex_amount = body_flex * tail_pos * body_width * 0.3
                        stripe_y += flex_amount
                    
                    stripe_points.append((stripe_x, stripe_y))
                
                # Alternate colors
                stripe_color = white if i % 2 == 0 else secondary_color
                
                # Draw the stripe
                pygame.draw.line(
                    screen,
                    stripe_color,
                    stripe_points[0],
                    stripe_points[1],
                    int(radius * 0.4)
                )
        
        # Add tail fin (fan-shaped)
        tail_x = position[0] - body_length/2 * 0.9
        
        # Create a fan-shaped tail
        tail_points = []
        num_tail_points = 5
        for i in range(num_tail_points):
            t = i / (num_tail_points - 1)
            tail_angle = (t - 0.5) * math.pi * 0.6
            
            # Calculate point position
            fan_x = tail_x - math.cos(tail_angle) * radius * 0.8
            fan_y = position[1] + math.sin(tail_angle) * radius
            
            # Apply body flex to tail
            flex_amount = body_flex * body_width * 0.5
            fan_y += flex_amount
            
            tail_points.append((fan_x, fan_y))
        
        # Get connection points with body
        body_idx_top = num_body_points // 4 * 3
        body_idx_bottom = num_body_points // 4 * 1
        
        # Complete tail polygon
        tail_points.insert(0, body_points[body_idx_top])
        tail_points.append(body_points[body_idx_bottom])
        
        # Draw the tail
        pygame.draw.polygon(screen, color, tail_points)
        
        # Add some tail fin details
        tail_stripes = 2
        for i in range(1, tail_stripes + 1):
            # Draw a subtle line
            if len(tail_points) > 4:  # Make sure we have enough points
                p1 = tail_points[1 + i]
                p2 = tail_points[-1 - i]
                pygame.draw.line(
                    screen,
                    (max(0, r - 20), max(0, g - 20), max(0, b - 20)),
                    p1, p2, 1
                )
        
        # Add pectoral fins
        fin_length = radius * 0.7
        
        # Top fin
        fin1_points = []
        body_top_idx = num_body_points // 8
        fin_start = body_points[body_top_idx]
        fin1_points.append(fin_start)
        
        # Calculate fin tip (45 degrees from body)
        fin_tip_x = fin_start[0] + math.cos(math.pi/4) * fin_length
        fin_tip_y = fin_start[1] + math.sin(math.pi/4) * fin_length
        fin1_points.append((fin_tip_x, fin_tip_y))
        
        # End point on body
        body_top_idx2 = (body_top_idx - 1) % num_body_points
        fin1_points.append(body_points[body_top_idx2])
        
        # Draw top fin
        pygame.draw.polygon(screen, color, fin1_points)
        
        # Bottom fin
        fin2_points = []
        body_bottom_idx = num_body_points // 8 * 7
        fin_start = body_points[body_bottom_idx]
        fin2_points.append(fin_start)
        
        # Calculate fin tip (-45 degrees from body)
        fin_tip_x = fin_start[0] + math.cos(-math.pi/4) * fin_length
        fin_tip_y = fin_start[1] + math.sin(-math.pi/4) * fin_length
        fin2_points.append((fin_tip_x, fin_tip_y))
        
        # End point on body
        body_bottom_idx2 = (body_bottom_idx + 1) % num_body_points
        fin2_points.append(body_points[body_bottom_idx2])
        
        # Draw bottom fin
        pygame.draw.polygon(screen, color, fin2_points)
        
        # Add eyes on both sides of head
        eye_offset_x = body_length/2 * 0.7
        eye_offset_y = body_width/2 * 0.6
        eye_radius = radius * 0.2
        
        # Left eye
        left_eye_x = position[0] + eye_offset_x
        left_eye_y = position[1] + eye_offset_y
        pygame.draw.circle(screen, (255, 255, 255), (left_eye_x, left_eye_y), eye_radius)
        pygame.draw.circle(screen, (0, 0, 0), (left_eye_x, left_eye_y), eye_radius * 0.5)
        
        # Right eye
        right_eye_x = position[0] + eye_offset_x
        right_eye_y = position[1] - eye_offset_y
        pygame.draw.circle(screen, (255, 255, 255), (right_eye_x, right_eye_y), eye_radius)
        pygame.draw.circle(screen, (0, 0, 0), (right_eye_x, right_eye_y), eye_radius * 0.5)
        
        # Add highlights
        pygame.draw.circle(screen, (255, 255, 255), 
                         (left_eye_x - eye_radius * 0.3, left_eye_y - eye_radius * 0.3), 
                         eye_radius * 0.2)
        pygame.draw.circle(screen, (255, 255, 255), 
                         (right_eye_x - eye_radius * 0.3, right_eye_y - eye_radius * 0.3), 
                         eye_radius * 0.2)
        
        # For predators, add dorsal fin
        if is_predator:
            dorsal_height = radius * 0.6
            
            # Draw dorsal fin (on top in top-down view)
            dorsal_points = []
            
            # Base points
            dorsal_base1 = (position[0] + radius * 0.5, position[1])
            dorsal_points.append(dorsal_base1)
            
            # Fin tip
            dorsal_tip = (position[0], position[1] - dorsal_height)
            dorsal_points.append(dorsal_tip)
            
            # Other base point
            dorsal_base2 = (position[0] - radius * 0.5, position[1])
            dorsal_points.append(dorsal_base2)
            
            # Draw dorsal fin
            pygame.draw.polygon(screen, color, dorsal_points)

    def _render_scoreboard(self):
        """Render the scoreboard panel."""
        # Draw background
        pygame.draw.rect(self.screen, self.colors['bg_darker'], self.scoreboard_rect)
        pygame.draw.rect(self.screen, self.colors['border'], self.scoreboard_rect, 2)
        
        # Draw title
        title_text = self.header_font.render("Scoreboard", True, self.colors['title'])
        title_rect = title_text.get_rect(centerx=self.scoreboard_rect.centerx, top=self.scoreboard_rect.top + 20)
        self.screen.blit(title_text, title_rect)
        
        # Get generation from scoreboard if available
        from scoreboard import Scoreboard
        scoreboard_generation = Scoreboard.get_current_generation()
        
        # Use the higher generation value (local or from scoreboard)
        display_generation = max(self.generation, scoreboard_generation)
        
        # Draw generation counter
        gen_text = self.header_font.render(f"Generation: {display_generation}", True, self.colors['title'])
        gen_rect = gen_text.get_rect(centerx=self.scoreboard_rect.centerx, top=title_rect.bottom + 20)
        self.screen.blit(gen_text, gen_rect)
        
        # Get top species from scoreboard
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
            
            # Draw koi icon - make it smaller and position it properly
            # Calculate a position that ensures the koi stays within the cell
            koi_x = card_rect.x + 28  # Adjusted x position
            koi_y = card_rect.y + 50  # Centered vertically in the card
            rank_pos = (koi_x, koi_y)
            color = self.get_species_color(species_id)
            
            # Reduced size for scoreboard display - fixed value instead of using record's size
            koi_size = 8  # Smaller fixed size to fit within the cell borders
            
            # Draw the koi with its actual properties but reduced size
            self.draw_koi_fish_detail(
                self.screen,
                rank_pos,
                color,
                koi_size,  # Use smaller fixed size
                num_fins=3,  # Reduced number of fins for smaller fish
                num_nodes=6,  # Reduced number of nodes for smaller fish
                is_predator=False,
                body_flex=0
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

    def draw_koi_fish(self, screen, position, color, size, is_predator, orientation=0, body_flex=0):
        x, y = position
        
        # Use provided orientation or default to 0 (facing right)
        angle = orientation if orientation is not None else 0
        
        # Draw vision cone (only if show_vision is True)
        if self.show_vision:
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
        
        # Calculate body dimensions for top-down view
        body_length = base_radius * 3
        body_width = base_radius * 1.8  # Wider for top-down view
        
        # Convert angle to radians
        rad_angle = math.radians(angle)
        
        # Draw main body - using oval shape for top-down view
        # Define points for the oval body shape
        num_body_points = 16  # More points for smoother oval
        body_points = []
        
        # Create points for the oval body shape
        for i in range(num_body_points):
            angle_around = 2 * math.pi * i / num_body_points
            
            # Calculate distance from center based on angle
            # Create oval shape that's longer than it is wide
            t = abs(math.sin(angle_around))  # 0 at sides, 1 at front/back
            
            # Taper the back (tail) end
            if angle_around > math.pi / 2 and angle_around < 3 * math.pi / 2:
                # This is the back half
                taper_factor = 0.7  # Reduce width at tail
            else:
                # This is the front half
                taper_factor = 1.0  # Full width at head
                
            # Apply body flex to create a natural swimming motion
            # The flex should bend the fish's body, more pronounced at the tail
            flex_amount = 0
            # Determine if this point is in the tail half
            is_tail_half = (angle_around > math.pi / 2 and angle_around < 3 * math.pi / 2)
            if is_tail_half:
                # Normalize position along tail (0 at middle, 1 at tail end)
                tail_pos = (angle_around - math.pi / 2) / math.pi
                # Apply sinusoidal curve for natural bend
                flex_amount = body_flex * tail_pos * body_width * 0.4
            
            # Calculate the point's position
            dx = math.cos(angle_around) * body_length/2 * taper_factor
            dy = math.sin(angle_around) * body_width/2
            
            # Apply flex to x-position
            if is_tail_half:
                dy += flex_amount
            
            # Rotate the point
            rotated_point = self._rotate_point((dx, dy), (0, 0), rad_angle)
            # Translate to final position
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
        
        # Apply patterns based on pattern type
        if pattern_type == 1:  # Two-tone (Kohaku)
            # Create points for center pattern
            pattern_width = body_width * 0.4  # Make pattern narrower
            pattern_points = []
            
            # Create an inner pattern shape
            for i in range(num_body_points):
                angle_around = 2 * math.pi * i / num_body_points
                
                # Calculate distance from center
                if angle_around > math.pi / 2 and angle_around < 3 * math.pi / 2:
                    # This is the back half
                    taper_factor = 0.6  # Taper more for pattern
                else:
                    # This is the front half
                    taper_factor = 0.9
                    
                # Calculate the point's position - smaller than the body
                dx = math.cos(angle_around) * body_length/2 * taper_factor * 0.7
                dy = math.sin(angle_around) * pattern_width/2 * 0.8
                
                # Apply same flex to pattern
                if angle_around > math.pi / 2 and angle_around < 3 * math.pi / 2:
                    # Normalize position along tail (0 at middle, 1 at tail end)
                    tail_pos = (angle_around - math.pi / 2) / math.pi
                    flex_amount = body_flex * tail_pos * pattern_width * 0.4
                    dy += flex_amount
                
                # Rotate the point
                rotated_point = self._rotate_point((dx, dy), (0, 0), rad_angle)
                # Translate to final position
                pattern_points.append((rotated_point[0] + x, rotated_point[1] + y))
            
            # Draw the pattern
            pygame.draw.polygon(screen, white, pattern_points)
            
        elif pattern_type == 2:  # Spotted (Bekko)
            # Add spots scattered across the body
            num_spots = random.randint(4, 8)
            for _ in range(num_spots):
                # Random position within oval body
                spot_angle = random.uniform(0, 2 * math.pi)
                spot_dist = random.uniform(0.2, 0.7) * body_length/2  # Distance from center
                
                # Calculate position and apply taper if in tail area
                if spot_angle > math.pi / 2 and spot_angle < 3 * math.pi / 2:
                    spot_dist *= 0.7  # Spots smaller near tail
                
                # Calculate spot position
                spot_x = math.cos(spot_angle) * spot_dist
                spot_y = math.sin(spot_angle) * spot_dist * (body_width/body_length)
                
                # Apply flex to spots in tail area
                if spot_angle > math.pi / 2 and spot_angle < 3 * math.pi / 2:
                    tail_pos = (spot_angle - math.pi / 2) / math.pi
                    flex_amount = body_flex * tail_pos * body_width * 0.4
                    spot_y += flex_amount
                
                # Rotate spot position
                rotated_spot = self._rotate_point((spot_x, spot_y), (0, 0), rad_angle)
                spot_pos = (rotated_spot[0] + x, rotated_spot[1] + y)
                
                # Random spot size
                spot_radius = random.uniform(0.15, 0.3) * base_radius
                
                # Draw the spot
                pygame.draw.circle(screen, secondary_color, spot_pos, spot_radius)
                
        elif pattern_type == 3:  # Striped (Showa)
            # Add stripes across the body
            num_stripes = random.randint(3, 5)
            for i in range(num_stripes):
                # Position stripe at even intervals along body
                stripe_pos = 0.2 + (i * 0.6 / num_stripes)  # Position along body length
                
                # Stripe points - draw a line across the body
                stripe_points = []
                for angle_offset in [-0.3, 0.3]:  # Slightly angled stripes
                    # Calculate position
                    stripe_x = body_length/2 - stripe_pos * body_length
                    stripe_y = body_width/2 * angle_offset
                    
                    # Apply flex if in tail area
                    if stripe_pos > 0.5:  # If in the tail half
                        tail_pos = (stripe_pos - 0.5) * 2  # Normalize to 0-1
                        flex_amount = body_flex * tail_pos * body_width * 0.4
                        stripe_y += flex_amount
                    
                    # Rotate and translate
                    rotated_point = self._rotate_point((stripe_x, stripe_y), (0, 0), rad_angle)
                    stripe_points.append((rotated_point[0] + x, rotated_point[1] + y))
                
                # Alternate stripe colors
                stripe_color = white if i % 2 == 0 else secondary_color
                
                # Draw the stripe with thickness
                pygame.draw.line(
                    screen,
                    stripe_color,
                    stripe_points[0],
                    stripe_points[1],
                    int(base_radius * 0.4)
                )
        
        # Add tail fin detail (fan-shaped)
        tail_points = []
        tail_x = -body_length/2 * 0.9  # Slightly inside the body to connect nicely
        
        # Create a fan-shaped tail
        num_tail_points = 5
        for i in range(num_tail_points):
            # Calculate positions on a fan curve
            t = i / (num_tail_points - 1)  # 0 to 1
            tail_angle = (t - 0.5) * math.pi * 0.6  # -30 to +30 degrees
            
            # Calculate point position
            fan_x = tail_x - math.cos(tail_angle) * base_radius * 0.9
            fan_y = math.sin(tail_angle) * base_radius * 1.2
            
            # Apply body flex to tail
            flex_amount = body_flex * body_width * 0.6
            fan_y += flex_amount
            
            # Rotate and translate
            rotated_point = self._rotate_point((fan_x, fan_y), (0, 0), rad_angle)
            tail_points.append((rotated_point[0] + x, rotated_point[1] + y))
        
        # Get the connection points with the body (where the tail meets the body)
        body_connection_top = body_points[num_body_points // 4 * 3]  # Approx. position
        body_connection_bottom = body_points[num_body_points // 4 * 1]  # Approx. position
        
        # Complete the tail polygon
        tail_points.insert(0, body_connection_top)
        tail_points.append(body_connection_bottom)
        
        # Draw the tail
        pygame.draw.polygon(screen, color, tail_points)
        
        # Add some tail fin details/lines
        tail_stripes = 3
        for i in range(1, tail_stripes):
            t = i / tail_stripes
            # Middle points on the fan
            p1 = tail_points[1 + i]
            p2 = tail_points[-2 - i]
            # Draw a subtle line
            pygame.draw.line(
                screen,
                (max(0, r - 20), max(0, g - 20), max(0, b - 20)),  # Slightly darker
                p1, p2, 1
            )
        
        # Add pectoral fins on sides
        fin_start_x = body_length/4  # Position along body
        fin_length = base_radius * 0.9
        
        # Top fin
        fin1_points = []
        # Start point on body
        body_top_idx = num_body_points // 8
        fin_start_point = body_points[body_top_idx]
        fin1_points.append(fin_start_point)
        
        # Fin tip
        fin_angle = rad_angle + math.pi/4  # 45 degrees from body
        fin_tip_x = fin_start_point[0] + math.cos(fin_angle) * fin_length
        fin_tip_y = fin_start_point[1] + math.sin(fin_angle) * fin_length
        fin1_points.append((fin_tip_x, fin_tip_y))
        
        # End point on body
        body_top_idx2 = num_body_points // 8 - 1
        fin1_points.append(body_points[body_top_idx2 if body_top_idx2 >= 0 else body_top_idx2 + num_body_points])
        
        # Draw top pectoral fin
        pygame.draw.polygon(screen, color, fin1_points)
        
        # Bottom fin
        fin2_points = []
        # Start point on body
        body_bottom_idx = num_body_points // 8 * 7
        fin_start_point = body_points[body_bottom_idx]
        fin2_points.append(fin_start_point)
        
        # Fin tip
        fin_angle = rad_angle - math.pi/4  # -45 degrees from body
        fin_tip_x = fin_start_point[0] + math.cos(fin_angle) * fin_length
        fin_tip_y = fin_start_point[1] + math.sin(fin_angle) * fin_length
        fin2_points.append((fin_tip_x, fin_tip_y))
        
        # End point on body
        body_bottom_idx2 = num_body_points // 8 * 7 + 1
        fin2_points.append(body_points[body_bottom_idx2 % num_body_points])
        
        # Draw bottom pectoral fin
        pygame.draw.polygon(screen, color, fin2_points)
        
        # Add eyes - for top-down view, eyes are on both sides of the head
        eye_offset_x = body_length/2 * 0.7  # Near the head
        eye_offset_y = body_width/2 * 0.6  # Slightly inside body edge
        eye_radius = base_radius * 0.2
        
        # Left eye position (rotated)
        left_eye_pos = self._rotate_point((eye_offset_x, eye_offset_y), (0, 0), rad_angle)
        left_eye_pos = (left_eye_pos[0] + x, left_eye_pos[1] + y)
        
        # Right eye position (rotated)
        right_eye_pos = self._rotate_point((eye_offset_x, -eye_offset_y), (0, 0), rad_angle)
        right_eye_pos = (right_eye_pos[0] + x, right_eye_pos[1] + y)
        
        # Draw eyes
        pygame.draw.circle(screen, (255, 255, 255), left_eye_pos, eye_radius)
        pygame.draw.circle(screen, (255, 255, 255), right_eye_pos, eye_radius)
        
        # Add pupils
        pygame.draw.circle(screen, (0, 0, 0), left_eye_pos, eye_radius * 0.5)
        pygame.draw.circle(screen, (0, 0, 0), right_eye_pos, eye_radius * 0.5)
        
        # Add highlights to eyes
        highlight_offset = eye_radius * 0.3
        pygame.draw.circle(screen, (255, 255, 255), 
                          (left_eye_pos[0] - highlight_offset, left_eye_pos[1] - highlight_offset), 
                          eye_radius * 0.25)
        pygame.draw.circle(screen, (255, 255, 255), 
                          (right_eye_pos[0] - highlight_offset, right_eye_pos[1] - highlight_offset), 
                          eye_radius * 0.25)
                          
        # Add predator features if needed
        if is_predator:
            # For predators, add more pronounced fins
            dorsal_x = 0  # Center of body
            dorsal_y = 0  # Center of body
            dorsal_height = base_radius * 0.7
            
            # Draw predator dorsal fin (on top in top-down view)
            dorsal_points = []
            
            # Base points on body
            dorsal_base1 = self._rotate_point((dorsal_x + base_radius * 0.5, 0), (0, 0), rad_angle)
            dorsal_base1 = (dorsal_base1[0] + x, dorsal_base1[1] + y)
            dorsal_points.append(dorsal_base1)
            
            # Fin tip
            dorsal_tip = self._rotate_point((dorsal_x, -dorsal_height), (0, 0), rad_angle)
            dorsal_tip = (dorsal_tip[0] + x, dorsal_tip[1] + y)
            dorsal_points.append(dorsal_tip)
            
            # Other base point
            dorsal_base2 = self._rotate_point((dorsal_x - base_radius * 0.5, 0), (0, 0), rad_angle)
            dorsal_base2 = (dorsal_base2[0] + x, dorsal_base2[1] + y)
            dorsal_points.append(dorsal_base2)
            
            # Draw the dorsal fin
            pygame.draw.polygon(screen, color, dorsal_points)
