
import pygame
from pygame.math import Vector2
from shape import Shape, EnemyShape, Rectangle, Triangle
from mover import Mover
from projectile import Projectile
import sys

SEPARATION_ITER = 2  # How many times to push shapes apart when they overlap

def in_range(a, b, r): # Helper function: checks if the distance between objects a and b is within range r

    return (a.pos - b.pos).length_squared() <= r * r

def run_game():
    
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("SpaceGame")

    clock = pygame.time.Clock()

    # --- Hangar UI setup ---
    preview_size = 40  # size of mini triangle preview
    hangar_previews = [
        {"preview_pos": pygame.Vector2(160, 565), "show_button": False, "button_rect": pygame.Rect(0,0,80,25)},
        {"preview_pos": pygame.Vector2(320, 565), "show_button": False, "button_rect": pygame.Rect(0,0,80,25)},
        {"preview_pos": pygame.Vector2(480, 565), "show_button": False, "button_rect": pygame.Rect(0,0,80,25)},
    ]
    font = pygame.font.SysFont(None, 20)



    # --- Main player (Rectangle with hangar) ---
    main_player = Rectangle((400, 300))

    # Player fleet initially only contains the rectangle
    player_shapes = [main_player]


    enemy_shapes = [
        EnemyShape((100, 100)),
        EnemyShape((700, 120)),
        EnemyShape((120, 500)),
    ]

    bullets = []

    selecting = False # Flag that indicates if the player is currently dragging a selection box with the mouse
    selection_start = (0, 0) # The starting mouse position where the left button was first pressed (selection begins here)
    selection_rect = pygame.Rect(0, 0, 0, 0) # Rectangle used to visually and logically represent the drag-selection area

    while True:
        dt = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                clicked_ui = False

                # Check deploy buttons
                for i, slot in enumerate(hangar_previews):
                    if slot["show_button"] and slot["button_rect"].collidepoint(event.pos):
                        if main_player.can_deploy(i):
                            new_tri = main_player.deploy(i)
                            if new_tri:
                                player_shapes.append(new_tri)
                        slot["show_button"] = False  # hide button after deploying
                        clicked_ui = True
                        break

                # Check mini previews
                if not clicked_ui:
                    for i, slot in enumerate(hangar_previews):
                        preview_rect = pygame.Rect(slot["preview_pos"].x - preview_size//2,
                                                slot["preview_pos"].y - preview_size//2,
                                                preview_size, preview_size)
                        if preview_rect.collidepoint(event.pos):
                            slot["show_button"] = not slot["show_button"] # show deploy button above this preview
                            clicked_ui = True
                            break

                # Start selection if clicked elsewhere
                if not clicked_ui:
                    selecting = True # Start drag-selection when the left mouse button is pressed
                    selection_start = event.pos # Remember the mouse position at the moment selection started
                    selection_rect = pygame.Rect(event.pos, (0, 0)) # Initialize the selection rectangle starting at the mouse position
                    for shape in player_shapes:
                        shape.selected = shape.point_inside(event.pos) # Select a single shape immediately if the click is directly on it (without drag)

            
            elif event.type == pygame.MOUSEMOTION and selecting:
                mx, my = event.pos # Current mouse position while dragging
                sx, sy = selection_start # The initial selection starting point (mouse down position)
                selection_rect.width = mx - sx # Update selection rectangle width based on how far the mouse moved horizontally
                selection_rect.height = my - sy # Update selection rectangle height based on how far the mouse moved vertically
           
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                selecting = False # Stop drag-selection when the left mouse button is released
                rect = selection_rect.copy()
                rect.normalize() # Ensure the rectangle has positive width and height regardless of drag direction
                if rect.width > 5 and rect.height > 5:
                    for shape in player_shapes:
                        shape.selected = rect.collidepoint(shape.pos) # Mark shapes as selected if their position is inside the final selection rectangle
            
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                # Collect all player shapes that are currently selected when right-click occurs
                selected_shapes = [s for s in player_shapes if s.selected]
                if selected_shapes:
                    # Calculate the average position (center) of all selected shapes (formation center)
                    center = sum((s.pos for s in selected_shapes), Vector2(0, 0)) / len(selected_shapes)
                    for s in selected_shapes:
                        s.mover.formation_offset = s.pos - center # Store each shape's offset from the formation center (to preserve relative positions)
                    center_target = Vector2(event.pos)  # Target point for the group movement is where the player right-clicked
                    for s in selected_shapes:
                        s.mover.set_target(center_target + s.mover.formation_offset) # Set individual targets so shapes move in formation relative to the clicked position

        # --- Update cooldowns ---
        for s in player_shapes + enemy_shapes:
            s.update_cooldown(dt)

        # --- Update movement ---
        for shape in player_shapes:
            shape.mover.update(dt)

        # Enemies: approach to within range, then hold
        for e in enemy_shapes:
            if player_shapes:
                closest = min(player_shapes, key=lambda p: (p.pos - e.pos).length_squared())
                dist = (closest.pos - e.pos).length()
                if dist > e.fire_range * 0.95:
                    e.mover.set_target(closest.pos)  # approach
                else:
                    e.mover.set_target(e.pos)  # hold & shoot
            e.mover.update(dt)

        # --- Auto-fire: both sides ---
        for p in player_shapes:
            if not enemy_shapes:
                break
            nearest = min(enemy_shapes, key=lambda e: (e.pos - p.pos).length_squared())
            if in_range(p, nearest, p.fire_range) and p.ready_to_fire():
                dirv = (nearest.pos - p.pos)
                bullets.append(Projectile(p.pos, dirv, damage=p.bullet_damage, color=(255,240,120), owner_is_enemy=False))
                p.reset_cooldown()

        for e in enemy_shapes:
            if not player_shapes:
                break
            nearest = min(player_shapes, key=lambda p: (p.pos - e.pos).length_squared())
            if in_range(e, nearest, e.fire_range) and e.ready_to_fire():
                dirv = (nearest.pos - e.pos)
                bullets.append(Projectile(e.pos, dirv, damage=e.bullet_damage, color=(255,120,120), owner_is_enemy=True, speed=Projectile.SPEED*0.9))
                e.reset_cooldown()

        # --- Update bullets & handle hits ---
        for b in bullets:
            b.update(dt)
            if not b.alive:
                continue
            if b.owner_is_enemy:
                hit = None
                for p in player_shapes:
                    if b.collides_with_shape(p):
                        hit = p
                        break
                if hit:
                    hit.take_damage(b.damage)
                    b.alive = False
            else:
                hit = None
                for e in enemy_shapes:
                    if b.collides_with_shape(e):
                        hit = e
                        break
                if hit:
                    hit.take_damage(b.damage)
                    b.alive = False

        # Cleanup
        bullets = [b for b in bullets if b.alive]
        player_shapes = [s for s in player_shapes if s.health > 0.0]
        enemy_shapes = [s for s in enemy_shapes if s.health > 0.0]

        # --- Collisions (residual): small damage from touching using class-level DPS ---
        for _ in range(SEPARATION_ITER):
            for i, a in enumerate(player_shapes):
                for b in player_shapes[i + 1:]:
                    Mover.separate_rotated(a, b)
            for i, a in enumerate(enemy_shapes):
                for b in enemy_shapes[i + 1:]:
                    Mover.separate_rotated(a, b)

        for p in player_shapes:
            for e in enemy_shapes:
                if p.collides_with(e):
                    dmg = Shape.COLLISION_DPS * dt
                    p.take_damage(dmg)
                    e.take_damage(dmg)
                    for _ in range(SEPARATION_ITER):
                        Mover.separate_rotated(p, e)

        # --- Draw ---
        screen.fill((20, 20, 26))
        for shape in player_shapes:
            shape.draw(screen, show_range=shape.selected)
        for enemy in enemy_shapes:
            enemy.draw(screen)

        for b in bullets:
            b.draw(screen)

        if selecting:
            temp = selection_rect.copy()
            temp.normalize()
            pygame.draw.rect(screen, (100, 255, 100), temp, 1)

        # --- Draw hangar previews & deploy buttons ---
        for i, slot in enumerate(hangar_previews):
            # Draw mini triangle preview
            tri_surf = pygame.Surface((preview_size, preview_size), pygame.SRCALPHA)
            color = (255, 200, 0) if main_player.hangar[i] else (100, 100, 100)
            pygame.draw.polygon(tri_surf, color, [(preview_size//2, 0), (0, preview_size), (preview_size, preview_size)])
            screen.blit(tri_surf, (slot["preview_pos"].x - preview_size//2, slot["preview_pos"].y - preview_size//2))

            # Draw deploy button above preview if active
            if slot["show_button"]:
                btn_rect = pygame.Rect(slot["preview_pos"].x - 40, slot["preview_pos"].y - 65, 80, 25)
                slot["button_rect"] = btn_rect
                pygame.draw.rect(screen, (40, 160, 40), btn_rect, border_radius=6)
                pygame.draw.rect(screen, (0, 0, 0), btn_rect, 2, border_radius=6)
                text = font.render("Deploy", True, (255, 255, 255))
                screen.blit(text, (btn_rect.x + 10, btn_rect.y + 3))


        pygame.display.flip()