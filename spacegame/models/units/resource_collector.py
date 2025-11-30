import pygame
from spacegame.models.units.fleet_unit import SpaceUnit
from spacegame.config import IMAGES_DIR

class ResourceCollector(SpaceUnit):
    """Small deployable resource collector light craft.
    
    Resource collectors can heal the health and armor of large ships by
    navigating to them and transferring resources over time.
    """

    # Healing configuration
    HEAL_RATE = 15.0  # health/armor healed per second
    HEAL_RANGE = 60.0  # must be within this distance to heal

    def shape_id(self):
        return "resource_collector"
    
    def get_tier(self) -> int:
        # tier is stored per ship instance; default 0 like other ships.
        return getattr(self, "tier", 0)

    def __init__(self, start_pos, collector_id=None, tier: int = 0, **kwargs):
        # per-ship tier value
        self.tier = tier
        # load resource collector sprite
        sprite = pygame.image.load(IMAGES_DIR + "/ResourceCollector.png").convert_alpha()
        # rotate so it faces like the other ships (to the right at angle 0)
        sprite = pygame.transform.rotate(sprite, -90)

        # scale down (adjust factor if you want a different size)
        scaled_sprite = pygame.transform.smoothscale(
            sprite,
            (sprite.get_width() // 24, sprite.get_height() // 24)
        )

        # use sprite size for collisions / drawing
        super().__init__(start_pos, ship_size=scaled_sprite.get_size(), **kwargs)
        self.base_surf = scaled_sprite

        # id in the ExpeditionShip's resource collector pool (if any)
        self.collector_id = collector_id

        # recall state
        self.recalling = False
        self.hangar_slot = None

        # Resource collectors do 0 damage
        self.bullet_damage = 0.0

        # ---- Healing state ----
        self.healing_target = None  # The ship being healed (or None)

    def start_healing(self, target):
        """Set the target ship to heal. This will cancel any previous healing."""
        self.healing_target = target
        # Navigate to the target
        self.mover.set_target(target.pos)

    def cancel_healing(self):
        """Cancel the current healing operation."""
        self.healing_target = None

    def is_healing(self) -> bool:
        """Return True if actively healing a target."""
        return self.healing_target is not None

    def update_healing(self, dt: float) -> None:
        """Update healing state: navigate to target, heal when in range, apply damage/armor healing."""
        if self.healing_target is None:
            return

        # Check if target is still alive
        if self.healing_target.health <= 0.0:
            self.cancel_healing()
            return

        # Distance to target
        dist = (self.healing_target.pos - self.pos).length()

        # If close enough, heal and stop moving; otherwise navigate
        if dist <= self.HEAL_RANGE:
            # Stop moving by setting target to current position
            self.mover.set_target(self.pos)
            # Apply healing to the target
            self._apply_healing(self.healing_target, dt)
        else:
            # Keep navigating to target
            self.mover.set_target(self.healing_target.pos)

    def _apply_healing(self, target, dt: float) -> None:
        """Apply healing over time to the target's health and armor."""
        heal_amount = self.HEAL_RATE * dt

        # Heal armor first if it exists and is damaged
        if getattr(target, "max_armor", 0) > 0:
            armor_deficit = target.max_armor - target.armor
            if armor_deficit > 0:
                armor_heal = min(heal_amount, armor_deficit)
                target.armor += armor_heal
                heal_amount -= armor_heal  # Remaining heal goes to health

        # Heal health if there's remaining heal amount
        if heal_amount > 0:
            health_deficit = target.max_health - target.health
            if health_deficit > 0:
                health_heal = min(heal_amount, health_deficit)
                target.health += health_heal
