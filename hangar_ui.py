import pygame

class HangarUI:
    """Manages hangar light craft previews and deploy/recall buttons for the main ship."""

    def __init__(self, font, preview_size=40):
        """Initialize hangar UI with a pygame font and preview size in pixels."""
        self.font = font
        self.preview_size = preview_size
        # hard-coded preview slot positions along the bottom of the screen
        self.hangar_slots = [
            {'preview_position': pygame.Vector2(160, 565), 'show_button': False, 'button_rect': pygame.Rect(0, 0, 80, 25)},
            {'preview_position': pygame.Vector2(320, 565), 'show_button': False, 'button_rect': pygame.Rect(0, 0, 80, 25)},
            {'preview_position': pygame.Vector2(480, 565), 'show_button': False, 'button_rect': pygame.Rect(0, 0, 80, 25)},
        ]

    def handle_mouse_button_down(self, mouse_pos, main_player, player_shapes):
        """Process a left mouse button click. Returns True if the click was consumed by the hangar UI."""
        clicked_ui = False

        # Check deploy / recall buttons
        for i, hangar_slot in enumerate(self.hangar_slots):
            if hangar_slot['show_button'] and hangar_slot['button_rect'].collidepoint(mouse_pos):
                if main_player.hangar[i]:
                    # DEPLOY
                    if main_player.can_deploy(i):
                        new_fighter = main_player.deploy(i)
                        if new_fighter:
                            player_shapes.append(new_fighter)
                else:
                    # RECALL
                    icpts = getattr(main_player, 'hangar_ships', [None, None, None])
                    fighter_ship = icpts[i] if i < len(icpts) else None
                    if fighter_ship is not None and fighter_ship in player_shapes and fighter_ship.health > 0.0:
                        fighter_ship.recalling = True
                        fighter_ship.selected = False  # stop being commanded by the player

                hangar_slot['show_button'] = False  # hide button after click
                clicked_ui = True
                break

        # Check mini previews
        if not clicked_ui:
            for i, hangar_slot in enumerate(self.hangar_slots):
                preview_rect = pygame.Rect(
                    hangar_slot['preview_position'].x - self.preview_size // 2,
                    hangar_slot['preview_position'].y - self.preview_size // 2,
                    self.preview_size, self.preview_size,
                )
                if preview_rect.collidepoint(mouse_pos):
                    # Toggle deploy/recall button visibility above this preview
                    hangar_slot['show_button'] = not hangar_slot['show_button']
                    clicked_ui = True
                    break

        return clicked_ui

    def draw(self, screen, main_player, player_shapes):
        """Draw hangar previews, health bars, and active deploy/recall buttons."""
        preview_size = self.preview_size
        font = self.font

        # --- Draw hangar previews & deploy/recall buttons ---
        for i, hangar_slot in enumerate(self.hangar_slots):
            icpt_surf = pygame.Surface((preview_size, preview_size), pygame.SRCALPHA)

            # figure out which light craft (if any) is linked to this slot
            icpts = getattr(main_player, 'hangar_ships', [None, None, None])
            fighter_ship = icpts[i] if i < len(icpts) else None

            if main_player.hangar[i]:
                # In hangar: show grey light craft
                color = (120, 120, 120)
            else:
                # Deployed: show real color if the light craft is alive
                if fighter_ship is not None and fighter_ship in player_shapes and fighter_ship.health > 0.0:
                    color = fighter_ship.color
                else:
                    # No live light craft for this slot -> dark grey, also no button
                    color = (60, 60, 60)
                    hangar_slot['show_button'] = False

            pygame.draw.polygon(
                icpt_surf,
                color,
                [(preview_size // 2, 0), (0, preview_size), (preview_size, preview_size)],
            )

            preview_x = hangar_slot['preview_position'].x - preview_size // 2
            preview_y = hangar_slot['preview_position'].y - preview_size // 2
            screen.blit(icpt_surf, (preview_x, preview_y))

            # Health bar under preview when deployed and alive
            if fighter_ship is not None and fighter_ship in player_shapes and fighter_ship.health > 0.0:
                bar_w = preview_size
                bar_h = 5
                pad = 4
                bar_x = preview_x
                bar_y = preview_y + preview_size + pad

                pct = fighter_ship.health / fighter_ship.max_health if fighter_ship.max_health > 0 else 0.0
                pct = max(0.0, min(1.0, pct))
                fill_w = int(bar_w * pct + 0.5)

                bg_rect = pygame.Rect(bar_x, bar_y, bar_w, bar_h)
                pygame.draw.rect(screen, (40, 40, 40), bg_rect, border_radius=3)

                if fill_w > 0:
                    fill_color = (50, 200, 70) if pct >= 0.5 else (220, 70, 70)
                    fill_rect = pygame.Rect(bar_x, bar_y, fill_w, bar_h)
                    pygame.draw.rect(screen, fill_color, fill_rect, border_radius=3)

                pygame.draw.rect(screen, (10, 10, 10), bg_rect, 1, border_radius=3)

            # Draw deploy/recall button above preview if active
            if hangar_slot['show_button']:
                btn_rect = pygame.Rect(
                    hangar_slot['preview_position'].x - 40,
                    hangar_slot['preview_position'].y - 65,
                    80, 25,
                )
                hangar_slot['button_rect'] = btn_rect

                if main_player.hangar[i]:
                    # light craft still in hangar
                    btn_color = (40, 160, 40)
                    label = 'Deploy'
                else:
                    # light craft already deployed
                    btn_color = (180, 40, 40)
                    label = 'Recall'

                pygame.draw.rect(screen, btn_color, btn_rect, border_radius=6)
                pygame.draw.rect(screen, (0, 0, 0), btn_rect, 2, border_radius=6)
                text = font.render(label, True, (255, 255, 255))
                screen.blit(text, (btn_rect.x + 10, btn_rect.y + 3))
