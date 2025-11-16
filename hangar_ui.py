import pygame

class HangarUI:
    """Manages hangar triangle previews and deploy/recall buttons for the main ship."""

    def __init__(self, font, preview_size=40):
        """Initialize hangar UI with a pygame font and preview size in pixels."""
        self.font = font
        self.preview_size = preview_size
        # hard-coded preview slot positions along the bottom of the screen
        self.slots = [
            {'preview_pos': pygame.Vector2(160, 565), 'show_button': False, 'button_rect': pygame.Rect(0, 0, 80, 25)},
            {'preview_pos': pygame.Vector2(320, 565), 'show_button': False, 'button_rect': pygame.Rect(0, 0, 80, 25)},
            {'preview_pos': pygame.Vector2(480, 565), 'show_button': False, 'button_rect': pygame.Rect(0, 0, 80, 25)},
        ]

    def handle_mouse_button_down(self, mouse_pos, main_player, player_shapes):
        """Process a left mouse button click. Returns True if the click was consumed by the hangar UI."""
        clicked_ui = False

        # Check deploy / recall buttons
        for i, slot in enumerate(self.slots):
            if slot['show_button'] and slot['button_rect'].collidepoint(mouse_pos):
                if main_player.hangar[i]:
                    # DEPLOY
                    if main_player.can_deploy(i):
                        new_tri = main_player.deploy(i)
                        if new_tri:
                            player_shapes.append(new_tri)
                else:
                    # RECALL
                    tris = getattr(main_player, 'hangar_triangles', [None, None, None])
                    tri_obj = tris[i] if i < len(tris) else None
                    if tri_obj is not None and tri_obj in player_shapes and tri_obj.health > 0.0:
                        tri_obj.recalling = True
                        tri_obj.selected = False  # stop being commanded by the player

                slot['show_button'] = False  # hide button after click
                clicked_ui = True
                break

        # Check mini previews
        if not clicked_ui:
            for i, slot in enumerate(self.slots):
                preview_rect = pygame.Rect(
                    slot['preview_pos'].x - self.preview_size // 2,
                    slot['preview_pos'].y - self.preview_size // 2,
                    self.preview_size, self.preview_size,
                )
                if preview_rect.collidepoint(mouse_pos):
                    # Toggle deploy/recall button visibility above this preview
                    slot['show_button'] = not slot['show_button']
                    clicked_ui = True
                    break

        return clicked_ui

    def draw(self, screen, main_player, player_shapes):
        """Draw hangar previews, health bars, and active deploy/recall buttons."""
        preview_size = self.preview_size
        font = self.font

        # --- Draw hangar previews & deploy/recall buttons ---
        for i, slot in enumerate(self.slots):
            tri_surf = pygame.Surface((preview_size, preview_size), pygame.SRCALPHA)

            # figure out which triangle (if any) is linked to this slot
            tris = getattr(main_player, 'hangar_triangles', [None, None, None])
            tri_obj = tris[i] if i < len(tris) else None

            if main_player.hangar[i]:
                # In hangar: show grey triangle
                color = (120, 120, 120)
            else:
                # Deployed: show real color if the triangle is alive
                if tri_obj is not None and tri_obj in player_shapes and tri_obj.health > 0.0:
                    color = tri_obj.color
                else:
                    # No live triangle for this slot -> dark grey, also no button
                    color = (60, 60, 60)
                    slot['show_button'] = False

            pygame.draw.polygon(
                tri_surf,
                color,
                [(preview_size // 2, 0), (0, preview_size), (preview_size, preview_size)],
            )

            preview_x = slot['preview_pos'].x - preview_size // 2
            preview_y = slot['preview_pos'].y - preview_size // 2
            screen.blit(tri_surf, (preview_x, preview_y))

            # Health bar under preview when deployed and alive
            if tri_obj is not None and tri_obj in player_shapes and tri_obj.health > 0.0:
                bar_w = preview_size
                bar_h = 5
                pad = 4
                bar_x = preview_x
                bar_y = preview_y + preview_size + pad

                pct = tri_obj.health / tri_obj.max_health if tri_obj.max_health > 0 else 0.0
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
            if slot['show_button']:
                btn_rect = pygame.Rect(
                    slot['preview_pos'].x - 40,
                    slot['preview_pos'].y - 65,
                    80, 25,
                )
                slot['button_rect'] = btn_rect

                if main_player.hangar[i]:
                    # triangle still in hangar
                    btn_color = (40, 160, 40)
                    label = 'Deploy'
                else:
                    # triangle already deployed
                    btn_color = (180, 40, 40)
                    label = 'Recall'

                pygame.draw.rect(screen, btn_color, btn_rect, border_radius=6)
                pygame.draw.rect(screen, (0, 0, 0), btn_rect, 2, border_radius=6)
                text = font.render(label, True, (255, 255, 255))
                screen.blit(text, (btn_rect.x + 10, btn_rect.y + 3))
