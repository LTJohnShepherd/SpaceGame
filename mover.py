
import pygame
import math
from pygame.math import Vector2

class Mover:
  
    def __init__(self, start_pos, size=(60, 30), speed=300, rotation_speed=360):
        self.pos = Vector2(start_pos)
        self.target = Vector2(start_pos)
        self.size = size
        self.speed = speed
        self.rotation_speed = rotation_speed
        self.angle = 0.0
        self.selected = False
        self.formation_offset = Vector2()

    def set_target(self, position):
        self.target = Vector2(position)

    def update(self, dt):
        """Move and rotate smoothly toward the target."""
        direction = self.target - self.pos
        distance = direction.length()

        if distance > 0.1:
            move_dist = self.speed * dt
            if move_dist >= distance:
                self.pos = self.target
            else:
                self.pos += direction.normalize() * move_dist

            desired_angle = math.degrees(math.atan2(-direction.y, direction.x))
            delta_angle = (desired_angle - self.angle + 180) % 360 - 180
            max_rotate = self.rotation_speed * dt

            if abs(delta_angle) < max_rotate:
                self.angle = desired_angle
            else:
                self.angle += max_rotate * (1 if delta_angle > 0 else -1)

    def point_inside(self, point):
        """Axis-aligned bounding box check around self.pos (centered)."""
        w, h = self.size
        rect = pygame.Rect(0, 0, w, h)
        rect.center = (int(self.pos.x), int(self.pos.y))
        return rect.collidepoint(point)

    # ---------------- Collision ----------------
    @staticmethod
    def separate_rotated(a_shape, b_shape):
        """
        Approximate oriented bounding box (OBB) collision resolver between two shapes.
        Each shape has a mover with pos, size, and angle.
        """
        a = a_shape.mover
        b = b_shape.mover

        rotated_a = pygame.transform.rotate(a_shape.base_surf, a.angle)
        rotated_b = pygame.transform.rotate(b_shape.base_surf, b.angle)
        rect_a = rotated_a.get_rect(center=a.pos)
        rect_b = rotated_b.get_rect(center=b.pos)

        if not rect_a.colliderect(rect_b):
            return

        dx = rect_a.centerx - rect_b.centerx
        dy = rect_a.centery - rect_b.centery
        overlap_x = (rect_a.width + rect_b.width) / 2 - abs(dx)
        overlap_y = (rect_a.height + rect_b.height) / 2 - abs(dy)

        if overlap_x <= 0 or overlap_y <= 0:
            return

        # Push direction along smaller overlap
        if overlap_x < overlap_y:
            push = Vector2(overlap_x / 2 * (1 if dx > 0 else -1), 0)
        else:
            push = Vector2(0, overlap_y / 2 * (1 if dy > 0 else -1))

        # Small damping to reduce jitter
        push *= 0.95
        a.pos += push
        b.pos -= push