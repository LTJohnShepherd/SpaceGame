
# projectile.py
import pygame
from pygame.math import Vector2

class Projectile:
    # ---- Class-level defaults ----
    """
    מחלקה: Projectile
    תפקיד: ראה/י תיעוד הפונקציות והמאפיינים מטה. 
    """
    SPEED = 600.0
    RADIUS = 4

    def __init__(self, pos, direction, *, speed=None, radius=None, damage=10.0, color=(255, 240, 120), lifetime=2.0, owner_is_enemy=False):
        self.pos = Vector2(pos)
        self.dir = Vector2(direction)
        if self.dir.length_squared() == 0:
            self.dir = Vector2(1, 0)
        else:
            self.dir = self.dir.normalize()
        self.speed = float(self.SPEED if speed is None else speed)
        self.radius = int(self.RADIUS if radius is None else radius)
        self.damage = float(damage)
        self.color = color
        self.life = float(lifetime)
        self.owner_is_enemy = owner_is_enemy
        self.alive = True

    def update(self, dt):
        if not self.alive:
            return
        self.pos += self.dir * self.speed * dt
        self.life -= dt
        if self.life <= 0:
            self.alive = False

    def draw(self, surface):
        if not self.alive:
            return
        pygame.draw.circle(surface, self.color, (int(self.pos.x), int(self.pos.y)), self.radius)

    def collides_with_shape(self, shape):
        # Circle vs shape-approx collision using shape's bounding circle
        dx = self.pos.x - shape.pos.x
        dy = self.pos.y - shape.pos.y
        dist2 = dx*dx + dy*dy
        hit_r = shape.bounding_radius()
        return dist2 <= (hit_r + self.radius) * (hit_r + self.radius)