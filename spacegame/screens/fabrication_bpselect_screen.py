import sys
import math
import pygame
from spacegame.config import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    UI_BG_COLOR,
    UI_TAB_HEIGHT,
    UI_SECTION_TEXT_COLOR,
    UI_TAB_UNDERLINE_COLOR,
    UI_TAB_TEXT_SELECTED,
    UI_TAB_TEXT_COLOR,
    UI_NAV_BG_COLOR,
    UI_NAV_LINE_COLOR,
    UI_ICON_BLUE,
)
from spacegame.config import PREVIEWS_DIR
from spacegame.models.blueprints.interceptorblueprint import BPInterceptor
from spacegame.ui.fleet_management_ui import draw_tier_icon
from spacegame.models.modules.fabricatormodule import get_fabricator_modules_for_ship
from spacegame.screens.fabrication_bpdetails_screen import fabrication_bpdetails_screen


def fabrication_bpselect_screen(main_player, player_fleet, selected_fabricator_index=0):
    # Use the existing display surface if present; otherwise create one.
    screen = pygame.display.get_surface()
    if screen is None:
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

    width, height = screen.get_size()

    # ---------- FONTS ----------
    title_font = pygame.font.Font(None, 40)
    tab_font = pygame.font.Font(None, 28)
    close_font = pygame.font.Font(None, 40)
    name_font = pygame.font.Font(None, 22)
    dmg_font = pygame.font.Font(None, 22)

    # ---------- TOP BAR ----------
    TOP_BAR_HEIGHT = 96

    # Title in the center of the top bar (moved slightly up to give more room to tabs)
    title_text = "FABRICATION"
    title_surf = title_font.render(title_text, True, UI_SECTION_TEXT_COLOR)
    title_rect = title_surf.get_rect(center=(width // 2, TOP_BAR_HEIGHT // 2 - 22))

    # Back arrow (left)
    arrow_size = 32
    back_arrow_rect = pygame.Rect(0, 0, arrow_size, arrow_size)
    back_arrow_rect.center = (40, TOP_BAR_HEIGHT // 1.3)

    # Close "X" (right)
    close_surf = close_font.render("X", True, (255, 160, 40))
    close_rect = close_surf.get_rect()
    close_rect.center = (width - 40, TOP_BAR_HEIGHT // 1.25)
    close_hit_rect = close_rect.inflate(16, 16)

    # ---------- TABS ----------
    tab_labels = ["STORAGE", "BRIDGE", "FABRICATION", "REFINING", "INTERNAL MODULES"]
    selected_tab = 2  # FABRICATION selected
    tab_spacing = 16

    tab_entries = []
    total_tabs_width = -tab_spacing
    # Measure and compute widths (icon + text + padding)
    icon_size = 24
    ICON_MARGIN = 10
    H_PADDING = 24

    for label in tab_labels:
        text_surf = tab_font.render(label, True, UI_TAB_TEXT_COLOR)
        text_width = text_surf.get_width()
        tab_width = icon_size + ICON_MARGIN + text_width + H_PADDING * 2
        tab_entries.append({"label": label, "text_surf": text_surf, "width": tab_width})
        total_tabs_width += tab_width + tab_spacing

    # Move tabs slightly lower so they are not too close to the title text
    tabs_y = TOP_BAR_HEIGHT - UI_TAB_HEIGHT - 4
    tabs_left = width // 2 - total_tabs_width // 2

    # Create rects for tabs
    x = tabs_left
    for entry in tab_entries:
        rect = pygame.Rect(x, tabs_y, entry["width"], UI_TAB_HEIGHT)
        entry["rect"] = rect
        x += entry["width"] + tab_spacing

    # ---------- FABRICATOR MODULE SLOTS (01 / 02 / ...) ----------
    fabricator_modules = get_fabricator_modules_for_ship()
    if not fabricator_modules:
        fabricator_modules = [None]

    # clamp incoming selected index to valid range
    if fabricator_modules:
        selected_fabricator_index = max(
            0, min(selected_fabricator_index, len(fabricator_modules) - 1)
        )
    else:
        selected_fabricator_index = 0

    # Geometry for the left card and index column (01 / 02 / ...)
    nav_top_y = tabs_y - 6
    nav_bottom_y = tabs_y + UI_TAB_HEIGHT + 6
    content_top = nav_bottom_y + 24

    LEFT_SHIFT = 20
    card_x = 40 - LEFT_SHIFT
    card_y = content_top
    card_w = int(width * 0.38)
    card_h = int(height * 0.64)
    card_rect = pygame.Rect(card_x, card_y, card_w, card_h)

    idx_size = 96
    idx_rect_base = pygame.Rect(card_rect.left + 16, card_rect.top + 16, idx_size, idx_size)
    IDX_V_SPACING = idx_size + 24

    idx_rects = [
        pygame.Rect(idx_rect_base.left, idx_rect_base.top + i * IDX_V_SPACING, idx_size, idx_size)
        for i in range(len(fabricator_modules))
    ]
    if not idx_rects:
        idx_rects.append(idx_rect_base)

    # ---------- SECTION / CARDS LAYOUT ----------
    section_width = int(width * 0.32)
    section_height = 56

    def centered_rect(cx, cy):
        return pygame.Rect(
            cx - section_width // 2,
            cy - section_height // 2,
            section_width,
            section_height,
        )

    # Layout / card constants reused from inventory screen style
    BOX_W = 260
    BOX_H = 80
    COLS = 3
    MARGIN_X = 18
    MARGIN_Y = 18

    # Scroll state (smooth) copied from inventory
    offset_y = 0.0
    offset_y_raw = 0.0
    SCROLL_STEP = 40
    SCROLL_SMOOTH = 0.25

    # Build blueprint categories (for now a single SHIPS category)
    categories = [
        ("SHIPS", [BPInterceptor()]),
    ]

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return selected_fabricator_index

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos

                if back_arrow_rect.collidepoint(mx, my):
                    return selected_fabricator_index

                if close_hit_rect.collidepoint(mx, my):
                    return "to_game"

                # Tabs
                for idx, entry in enumerate(tab_entries):
                    if entry["rect"].collidepoint(mx, my):
                        label = entry["label"]
                        # Open Storage (Inventory) when STORAGE tab clicked
                        if label == "STORAGE":
                            from spacegame.screens.inventory import inventory_screen

                            res = inventory_screen(main_player, player_fleet)
                            if res == "to_game":
                                return "to_game"
                            # return focus back to FABRICATION tab after closing inventory
                            selected_tab = 2
                        elif label == "INTERNAL MODULES":
                            from spacegame.screens.internal_modules_screen import internal_modules_screen

                            res = internal_modules_screen(main_player, player_fleet)
                            if res == "to_game":
                                return "to_game"
                            # after closing, go back to FABRICATION tab highlight
                            selected_tab = 2
                        else:
                            selected_tab = idx
                        break

                # Fabricator slot buttons (01 / 02 / ...)
                for i, rect in enumerate(idx_rects):
                    if rect.collidepoint(mx, my):
                        selected_fabricator_index = i
                        break

                # Blueprint card clicks → open DETAILS SCREEN
                for i, rect in enumerate(card_rects):
                    if i >= len(blueprints):
                        continue

                    draw_rect = rect.move(0, offset_y)  # apply scroll offset

                    if draw_rect.collidepoint(mx, my):
                        bp = blueprints[i]

                        # Call the DETAILS screen
                        res = fabrication_bpdetails_screen(
                            main_player,
                            player_fleet,
                            selected_fabricator_index,
                            bp
                        )

                        # Sync return value
                        if res == "to_game":
                            return "to_game"
                        elif isinstance(res, int):
                            selected_fabricator_index = res

                        break


            # Mouse wheel support (pygame 2) and legacy wheel buttons
            if event.type == pygame.MOUSEWHEEL:
                offset_y_raw += event.y * SCROLL_STEP
            if event.type == pygame.MOUSEBUTTONDOWN and event.button in (4, 5):
                # legacy mouse wheel: 4=up, 5=down
                if event.button == 4:   # wheel up
                    offset_y_raw += SCROLL_STEP
                else:                   # wheel down
                    offset_y_raw -= SCROLL_STEP

        # ---------- DRAW ----------
        screen.fill(UI_BG_COLOR)

        # Nav band coordinates
        nav_top_y = tabs_y - 6
        nav_bottom_y = tabs_y + UI_TAB_HEIGHT + 6

        # Brighter strip behind all nav text/buttons
        pygame.draw.rect(
            screen,
            UI_NAV_BG_COLOR,
            (0, nav_top_y, width, nav_bottom_y - nav_top_y),
        )

        # Lines above and below the nav/tab area
        pygame.draw.line(screen, UI_NAV_LINE_COLOR, (0, nav_top_y), (width, nav_top_y), 1)
        pygame.draw.line(
            screen, UI_NAV_LINE_COLOR, (0, nav_bottom_y), (width, nav_bottom_y), 1
        )

        # Title (on top of nav background)
        screen.blit(title_surf, title_rect)

        # Back arrow (on top of nav background)
        arrow_color = (220, 235, 255)
        arrow_points = [
            (back_arrow_rect.left, back_arrow_rect.centery),
            (back_arrow_rect.right, back_arrow_rect.top),
            (back_arrow_rect.right, back_arrow_rect.bottom),
        ]
        pygame.draw.polygon(screen, arrow_color, arrow_points)

        # Close X (on top of nav background)
        screen.blit(close_surf, close_rect)

        # Tabs (transparent background: only icon, text, highlight on nav lines)
        for idx, entry in enumerate(tab_entries):
            rect = entry["rect"]
            is_selected = idx == selected_tab

            icon_rect = pygame.Rect(0, 0, icon_size, icon_size)
            icon_rect.centery = rect.centery
            icon_rect.left = rect.left + H_PADDING
            pygame.draw.rect(
                screen,
                (210, 220, 235) if is_selected else (170, 190, 210),
                icon_rect,
                border_radius=4,
                width=2,
            )

            text_color = UI_TAB_TEXT_SELECTED if is_selected else UI_TAB_TEXT_COLOR
            label_surf = tab_font.render(entry["label"], True, text_color)
            label_rect = label_surf.get_rect()
            label_rect.centery = rect.centery
            label_rect.left = icon_rect.right + ICON_MARGIN
            screen.blit(label_surf, label_rect)

            if is_selected:
                # highlight segments exactly on the top/bottom nav lines
                pygame.draw.line(
                    screen,
                    UI_TAB_UNDERLINE_COLOR,
                    (rect.left + 6, nav_top_y),
                    (rect.right - 6, nav_top_y),
                    2,
                )
                pygame.draw.line(
                    screen,
                    UI_TAB_UNDERLINE_COLOR,
                    (rect.left + 6, nav_bottom_y),
                    (rect.right - 6, nav_bottom_y),
                    2,
                )

        # ---------- MAIN CONTENT (fabrication visual) ----------
        content_top = nav_bottom_y + 24

        # Left detail: index squares (01, 02, ...) with corner-only decoration + progress bar.
        def draw_index_square(rect: pygame.Rect, label: str, selected: bool) -> None:
            corner_len = 18
            corner_thick = 3
            corner_color = UI_TAB_UNDERLINE_COLOR if selected else UI_TAB_TEXT_SELECTED

            # top-left
            pygame.draw.line(
                screen,
                corner_color,
                (rect.left, rect.top),
                (rect.left + corner_len, rect.top),
                corner_thick,
            )
            pygame.draw.line(
                screen,
                corner_color,
                (rect.left, rect.top),
                (rect.left, rect.top + corner_len),
                corner_thick,
            )

            # top-right
            pygame.draw.line(
                screen,
                corner_color,
                (rect.right - corner_len, rect.top),
                (rect.right, rect.top),
                corner_thick,
            )
            pygame.draw.line(
                screen,
                corner_color,
                (rect.right, rect.top),
                (rect.right, rect.top + corner_len),
                corner_thick,
            )

            # bottom-left
            pygame.draw.line(
                screen,
                corner_color,
                (rect.left, rect.bottom - corner_len),
                (rect.left, rect.bottom),
                corner_thick,
            )
            pygame.draw.line(
                screen,
                corner_color,
                (rect.left, rect.bottom),
                (rect.left + corner_len, rect.bottom),
                corner_thick,
            )

            # bottom-right (fixed to be a real corner)
            pygame.draw.line(
                screen,
                corner_color,
                (rect.right - corner_len, rect.bottom),
                (rect.right, rect.bottom),
                corner_thick,
            )
            pygame.draw.line(
                screen,
                corner_color,
                (rect.right, rect.bottom - corner_len),
                (rect.right, rect.bottom),
                corner_thick,
            )

            index_font = pygame.font.Font(None, 36)
            idx_text = index_font.render(label, True, corner_color)
            it_rect = idx_text.get_rect(center=rect.center)
            screen.blit(idx_text, it_rect)

        # Draw all slot squares (01 / 02 / ...)
        for i, r in enumerate(idx_rects, start=1):
            draw_index_square(r, f"{i:02d}", selected=(i - 1) == selected_fabricator_index)

        # Progress bar inside ALL squares
        fabrication_progress = 0.0  # 0 = idle, >0 once fabrication has started
        pb_margin = 12
        PROGRESS_COLOR = (255, 160, 40)  # same orange as nav X

        for r in idx_rects:
            pb_rect = pygame.Rect(
                r.left + pb_margin,
                r.bottom - 22,
                r.width - pb_margin * 2,
                12,
            )
            pygame.draw.rect(screen, (40, 50, 70), pb_rect)

            if fabrication_progress > 0.0:
                inner_w = max(2, int(pb_rect.width * fabrication_progress))
                inner_rect = pygame.Rect(pb_rect.left, pb_rect.top, inner_w, pb_rect.height)
                pygame.draw.rect(screen, PROGRESS_COLOR, inner_rect)


        # ---------- Right-hand area: categories + blueprint cards (inventory style)
        # We'll render the first category (SHIPS) for now.
        if idx_rects:
            base_idx_rect = idx_rects[0]
        else:
            base_idx_rect = idx_rect_base

        details_x = base_idx_rect.right + 18
        details_y = base_idx_rect.top

        # Title for the category
        cat_title_font = pygame.font.Font(None, 32)
        cat_title = cat_title_font.render(categories[0][0], True, UI_SECTION_TEXT_COLOR)
        cat_title_rect = cat_title.get_rect()
        cat_title_rect.topleft = (details_x, details_y)
        screen.blit(cat_title, cat_title_rect)

        # Layout for cards: start below title, aligned to the right of the "01" rect
        cards_top_y = cat_title_rect.bottom + 18

        def layout_rects(num_items, top_y, left_start):
            rects = []
            for i in range(num_items):
                row = i // COLS
                col = i % COLS
                x = left_start + col * (BOX_W + MARGIN_X)
                y = top_y + row * (BOX_H + MARGIN_Y)
                rects.append(pygame.Rect(x, y, BOX_W, BOX_H))
            return rects

        # Build blueprint list for display
        blueprints = categories[0][1]

        # displays the cards
        if len(blueprints) == 0:
            display_count = COLS
        else:
            remainder = len(blueprints) % COLS
            if remainder == 0:
                display_count = len(blueprints)
            else:
                display_count = len(blueprints) + (COLS - remainder)

        left_start = details_x
        card_rects = layout_rects(display_count, cards_top_y, left_start)

        # Scroll bounds (same logic as inventory)
        scroll_area_top = nav_bottom_y + 4
        content_top_unscrolled = cards_top_y
        if card_rects:
            content_bottom = card_rects[-1].bottom + 40
        else:
            content_bottom = content_top_unscrolled

        visible_height = SCREEN_HEIGHT - scroll_area_top
        total_content_height = content_bottom - content_top_unscrolled
        if total_content_height <= visible_height:
            bottom_limit = 0.0
        else:
            bottom_limit = scroll_area_top - total_content_height

        # Clamp & smooth scroll
        target = max(min(offset_y_raw, 0.0), bottom_limit)
        offset_y += (target - offset_y) * SCROLL_SMOOTH
        if abs(target - offset_y) < 0.5:
            offset_y = target
        offset_y_raw = target

        # Clip to scroll area
        scroll_clip_rect = pygame.Rect(0, scroll_area_top, width, height - scroll_area_top)
        screen.set_clip(scroll_clip_rect)

        # Draw cards (either blueprints or placeholders)
        for i, rect in enumerate(card_rects):
            draw_rect = rect.move(0, offset_y)
            # If we have a blueprint for this slot, draw it; otherwise placeholder
            if i < len(blueprints):
                bp = blueprints[i]
                # card background + border
                pygame.draw.rect(screen, (30, 40, 70), draw_rect, border_radius=0)
                pygame.draw.rect(screen, UI_ICON_BLUE, draw_rect, 2, border_radius=0)

                # tier flag
                tier_value = getattr(bp, "tier", 0)
                draw_tier_icon(screen, draw_rect, tier_value)

                # preview image (load by filename)
                try:
                    img = pygame.image.load(PREVIEWS_DIR + "/" + bp.preview_filename)
                    img = pygame.transform.smoothscale(img, (48, 48))
                    img_rect = img.get_rect(
                        center=(draw_rect.x + 40, draw_rect.y + draw_rect.height // 2)
                    )
                    screen.blit(img, img_rect.topleft)
                except Exception:
                    # fallback: small empty box
                    placeholder = pygame.Surface((48, 48))
                    placeholder.fill((40, 40, 60))
                    screen.blit(placeholder, (draw_rect.x + 16, draw_rect.y + 16))

                # name
                line1_surf = name_font.render("INTERCEPTOR", True, (230, 230, 255))
                line2_surf = name_font.render("SQUADRON", True, (230, 230, 255))
                screen.blit(line1_surf, (draw_rect.x + 110, draw_rect.y + 20))
                screen.blit(line2_surf, (draw_rect.x + 110, draw_rect.y + 40))

                # amount
                qty = bp.quantity
                if qty is None or (isinstance(qty, float) and math.isinf(qty)):
                    qty_text = "INF"
                else:
                    qty_text = f"{int(qty):,}"
                qty_surf = dmg_font.render(qty_text, True, (108, 198, 219))
                screen.blit(qty_surf, (draw_rect.x + 60, draw_rect.y + 50))
            else:
                # placeholder card
                pygame.draw.rect(screen, (20, 35, 60), draw_rect, border_radius=0)
                pygame.draw.rect(screen, (60, 100, 150), draw_rect, 1, border_radius=0)

        # reset clip
        screen.set_clip(None)

        pygame.display.flip()