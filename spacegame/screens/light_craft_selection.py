import pygame
import sys
from spacegame.ui.ui import Button, INTERCEPTOR_PREVIEW_IMG
from spacegame.models.units.interceptor import Interceptor

def light_craft_selection_screen(main_player, slot_index: int):
    screen = pygame.display.get_surface()
    if screen is None:
        return

    clock = pygame.time.Clock()
    width, height = screen.get_size()

    title_font = pygame.font.Font(None, 48)
    section_font = pygame.font.Font(None, 32)
    name_font = pygame.font.Font(None, 28)
    dmg_font = pygame.font.Font(None, 22)
    btn_font = pygame.font.Font(None, 28)

    back_btn = Button((10, 10, 100, 32), "Back", btn_font)

    # ---- helpers to modify assignments ----
    def clear_slot():
        if 0 <= slot_index < len(main_player.hangar_assignments):
            main_player.hangar_assignments[slot_index] = None
        if 0 <= slot_index < len(main_player.hangar):
            main_player.hangar[slot_index] = False
        if 0 <= slot_index < len(main_player.hangar_ships):
            main_player.hangar_ships[slot_index] = None

    def assign_interceptor(icpt_id: int):
        if 0 <= slot_index < len(main_player.hangar_assignments):
            main_player.hangar_assignments[slot_index] = icpt_id
        if 0 <= slot_index < len(main_player.hangar):
            main_player.hangar[slot_index] = True
        if 0 <= slot_index < len(main_player.hangar_ships):
            ship = main_player.hangar_ships[slot_index]
            if ship is None or ship.health <= 0.0:
                main_player.hangar_ships[slot_index] = None

    # ---- layout helpers ----
    BOX_W = 260
    BOX_H = 80
    COLS = 3
    MARGIN_X = 18
    MARGIN_Y = 18

    def layout_rects(num_items, top_y):
        total_w = COLS * BOX_W + (COLS - 1) * MARGIN_X
        left_start = width // 2 - total_w // 2
        rects = []
        for i in range(num_items):
            row = i // COLS
            col = i % COLS
            x = left_start + col * (BOX_W + MARGIN_X)
            y = top_y + row * (BOX_H + MARGIN_Y)
            rects.append(pygame.Rect(x, y, BOX_W, BOX_H))
        return rects

        # ---- tier helpers ----
    ICON_BLUE = (70, 130, 220)
    ICON_WHITE = (240, 240, 255)

    def tier_to_roman(tier_value: int) -> str:
        if tier_value <= 0:
            return "0"
        numerals = ["", "I", "II", "III"]
        if tier_value < len(numerals):
            return numerals[tier_value]
        # fallback nums
        return numerals[-1] + f"+{tier_value - (len(numerals) - 1)}"

    def draw_tier_icon(surface, rect, tier_value):
        """
        Blue flag in the top-right corner.
        Inside it – large centered roman numeral (no white inner box).
        """

        # make the font larger and clearer
        large_tier_font = pygame.font.Font(None, 26)

        # smaller, tighter flag
        flag_w = 22
        flag_h = 22
        flag_rect = pygame.Rect(rect.right - flag_w - 1, rect.top + 1, flag_w, flag_h)

        # draw blue box
        pygame.draw.rect(surface, ICON_BLUE, flag_rect)

        # convert tier to roman numerals
        text = tier_to_roman(int(tier_value))

        # render large, centered numeral
        tier_text = large_tier_font.render(text, True, ICON_WHITE)

        # clean perfect centering
        tier_rect = tier_text.get_rect(center=flag_rect.center)

        surface.blit(tier_text, tier_rect)

    # we will recompute rects every frame (simple)
    running = True
    while running:

        # recompute alive/selected/stored every frame
        hangar = getattr(main_player, "hangar_system", None)
        if hangar is not None:
            alive_entries = hangar.alive_pool_entries()
            selected_ids = hangar.selected_interceptor_ids()
        else:
            pool = getattr(main_player, "interceptor_pool", [])
            assignments = getattr(main_player, "hangar_assignments", [])
            alive_entries = [e for e in pool if e.get("alive", False)]

            selected_ids = set()
            for assigned_id in assignments:
                if assigned_id is None:
                    continue
                for e in alive_entries:
                    if e.get("id") == assigned_id:
                        selected_ids.add(assigned_id)
                        break

        selected_items = [e for e in alive_entries if e.get("id") in selected_ids]
        stored_items   = [e for e in alive_entries if e.get("id") not in selected_ids]

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            if back_btn.handle_event(event):
                return

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos

                selected_count = 1 + len(selected_items)   # 1 for "None"
                top_selected_y = 130
                selected_rects = layout_rects(selected_count, top_selected_y)

                none_rect = selected_rects[0]
                selected_craft_rects = selected_rects[1:]

                stored_title_y = (
                    (selected_rects[-1].bottom + 40)
                    if selected_rects
                    else (top_selected_y + 40)
                )
                stored_rects = layout_rects(len(stored_items), stored_title_y + 40)

                # 1) "None" button (first in selected list)
                if none_rect.collidepoint(mx, my):
                    clear_slot()
                    return

                # 2) Selected crafts are NOT selectable (just visual) – skip

                # 3) Stored crafts ARE selectable
                for rect, entry in zip(stored_rects, stored_items):
                    if rect.collidepoint(mx, my):
                        assign_interceptor(entry["id"])
                        return

        screen.fill((12, 12, 20))

        # main title
        t = title_font.render("Light Craft Selection", True, (255, 255, 255))
        screen.blit(t, (width // 2 - t.get_width() // 2, 40))

        back_btn.draw(screen)

        # ---- Selected crafts section ----
        selected_title = section_font.render("Selected crafts", True, (220, 220, 255))
        selected_title_y = 90
        screen.blit(selected_title, (width // 2 - selected_title.get_width() // 2, selected_title_y))

        selected_count = 1 + len(selected_items)   # "None" + selected entries
        top_selected_y = 130
        selected_rects = layout_rects(selected_count, top_selected_y)

        if selected_rects:
            none_rect = selected_rects[0]
            selected_craft_rects = selected_rects[1:]
        else:
            none_rect = None
            selected_craft_rects = []

        # draw "None" (first selected box) – sharp corners
        if none_rect is not None:
            pygame.draw.rect(screen, (30, 40, 70), none_rect, border_radius=0)
            pygame.draw.rect(screen, (200, 80, 80), none_rect, 2, border_radius=0)

            # circle with X, offset from left
            preview_x = none_rect.x + 40
            preview_y = none_rect.y + none_rect.height // 2

            pygame.draw.circle(screen, (200, 60, 60), (preview_x, preview_y), 22, 3)
            pygame.draw.line(
                screen, (200, 60, 60),
                (preview_x - 12, preview_y - 12),
                (preview_x + 12, preview_y + 12), 3
            )
            pygame.draw.line(
                screen, (200, 60, 60),
                (preview_x + 12, preview_y - 12),
                (preview_x - 12, preview_y + 12), 3
            )

            name = name_font.render("None", True, (230, 230, 255))
            screen.blit(name, (preview_x + 50, none_rect.y + 24))

        # draw selected crafts (visual only)
        for rect, entry in zip(selected_craft_rects, selected_items):
            pygame.draw.rect(screen, (30, 40, 70), rect, border_radius=0)
            pygame.draw.rect(screen, ICON_BLUE, rect, 2, border_radius=0)  # border matches icon color

            tier_value = entry.get("tier", 0)
            draw_tier_icon(screen, rect, tier_value)

            preview_x = rect.x + 40
            preview_y = rect.y + rect.height // 2

            # preview image
            img = pygame.transform.smoothscale(INTERCEPTOR_PREVIEW_IMG, (48, 48))
            rect_img = img.get_rect(center=(preview_x, preview_y))
            screen.blit(img, rect_img.topleft)

            name = name_font.render(entry["name"], True, (230, 230, 255))
            screen.blit(name, (preview_x + 50, rect.y + 12))

            dmg = Interceptor.DEFAULT_BULLET_DAMAGE
            dmg_text = dmg_font.render(f"Damage: {int(dmg)}", True, (200, 200, 220))
            screen.blit(dmg_text, (preview_x + 50, rect.y + 44))

        # ---- Stored crafts section ----
        stored_title_y = (
            (selected_rects[-1].bottom + 40)
            if selected_rects
            else (top_selected_y + 40)
        )

        stored_title = section_font.render("Stored crafts", True, (220, 220, 255))
        screen.blit(stored_title, (width // 2 - stored_title.get_width() // 2, stored_title_y))

        stored_rects = layout_rects(len(stored_items), stored_title_y + 40)

        for rect, entry in zip(stored_rects, stored_items):
            pygame.draw.rect(screen, (30, 40, 70), rect, border_radius=0)
            pygame.draw.rect(screen, ICON_BLUE, rect, 2, border_radius=0)  # border matches icon color

            tier_value = entry.get("tier", 0)
            draw_tier_icon(screen, rect, tier_value)

            preview_x = rect.x + 40
            preview_y = rect.y + rect.height // 2

            # preview image
            img = pygame.transform.smoothscale(INTERCEPTOR_PREVIEW_IMG, (48, 48))
            rect_img = img.get_rect(center=(preview_x, preview_y))
            screen.blit(img, rect_img.topleft)

            name = name_font.render(entry["name"], True, (230, 230, 255))
            screen.blit(name, (preview_x + 50, rect.y + 12))

            dmg = Interceptor.DEFAULT_BULLET_DAMAGE
            dmg_text = dmg_font.render(f"Damage: {int(dmg)}", True, (200, 200, 220))
            screen.blit(dmg_text, (preview_x + 50, rect.y + 44))

        pygame.display.flip()
        clock.tick(60)