import pygame
from pygame.math import Vector2
from spacegame.config import (
    PROJECTILE_SPEED,
    PROJECTILE_RADIUS,
    PROJECTILE_LIFETIME,
)

class Projectile:
    # ---- Class-level defaults ----
    """
    Projectile
    """
    SPEED = PROJECTILE_SPEED
    RADIUS = PROJECTILE_RADIUS

    def __init__(self, pos, direction, *, speed=None, radius=None,
                 hull_damage=None, armor_damage=None,
                 color=(255, 240, 120), lifetime=PROJECTILE_LIFETIME,
                 owner_is_enemy=False):
        self.pos = Vector2(pos)
        self.direction = Vector2(direction)
        if self.direction.length_squared() == 0:
            self.direction = Vector2(1, 0)
        else:
            self.direction = self.direction.normalize()
        self.speed = float(self.SPEED if speed is None else speed)
        self.radius = int(self.RADIUS if radius is None else radius)

        # Hull & armor damage
        if hull_damage is None:
            hull_damage = 10.0
        if armor_damage is None:
            armor_damage = hull_damage

        self.hull_damage = float(hull_damage)
        self.armor_damage = float(armor_damage)
        self.color = color
        self.lifetime = float(lifetime)
        self.owner_is_enemy = owner_is_enemy
        self.is_active = True

    def update(self, dt):
        if not self.is_active:
            return
        self.pos += self.direction * self.speed * dt
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.is_active = False

    def draw(self, surface):
        if not self.is_active:
            return
        pygame.draw.circle(surface, self.color, (int(self.pos.x), int(self.pos.y)), self.radius)

    def collides_with_shape(self, spaceship):
        # Circle vs sprite mask collision detection
        # Get the sprite surface and mask from the spaceship
        surf, mask = spaceship.get_rotated_sprite()
        rect = spaceship.get_sprite_rect(surf)
        
        # Check if projectile circle overlaps with the sprite mask
        # We need to check multiple points around the projectile circle
        # or use a circle-mask collision approach
        projectile_rect = pygame.Rect(
            int(self.pos.x - self.radius),
            int(self.pos.y - self.radius),
            self.radius * 2,
            self.radius * 2
        )
        
        # Check if rects overlap first (broad phase)
        if not projectile_rect.colliderect(rect):
            return False
        
        # Narrow phase: check mask collision by testing points on projectile circle
        # Test center and points around the circle perimeter
        import math
        test_points = [(0, 0)]  # center
        steps = 16
        for i in range(steps):
            angle = 2 * math.pi * i / steps
            px = int(self.pos.x + self.radius * math.cos(angle))
            py = int(self.pos.y + self.radius * math.sin(angle))
            test_points.append((px, py))
        
        for px, py in test_points:
            # Convert to mask-local coordinates
            local_x = px - rect.left
            local_y = py - rect.top
            
            # Check bounds and mask
            if (0 <= local_x < mask.get_size()[0] and
                0 <= local_y < mask.get_size()[1]):
                if mask.get_at((local_x, local_y)):
                    return True
        
        return False