
import pygame
import sys
from gameScreen import run_game

# ---------- UI helpers ----------
class Button:

    def __init__(self, rect, text, font, base_color=(170,170,170), hover_color=(220,220,220), text_color=(0,0,0)):
        self.rect = pygame.Rect(rect) #pygame.Rect(left, top, width, height) , rect is a tupple with those values, pygame.Rect() create a Rect object for the button (stores position and size)
        self.text = text #text for the button
        self.font = font
        self.base_color = base_color # the color of the button
        self.hover_color = hover_color # the color of the button when you hover on it with the mouse.
        self.text_color = text_color 

    def draw(self, surface):# surface: the screen you want to draw on

        mouse_pos = pygame.mouse.get_pos() #position of the mouse on the screen

        if self.rect.collidepoint(mouse_pos): # set button color depending on mouse hover
            color = self.hover_color
        else:
            color = self.base_color

        pygame.draw.rect(surface, color, self.rect, border_radius=12) # pygame.draw.rect(surface, color, rect (object), width=0, border_radius=0)
        
        label = self.font.render(self.text, True, self.text_color) # render the button text into a new surface (text becomes an image that can be drawn)
        
        label_rect = label.get_rect(center=self.rect.center) # create a Rect for the text surface and center it inside the button's rectangle
        
        surface.blit(label, label_rect) # draw (blit) the rendered text onto the target surface at the calculated position

    # Handle mouse click events: returns True if the left mouse button was pressed
    # while the cursor is positioned over the button; otherwise returns False.
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return True
        return False

def main():
   
    pygame.init() # Initialize all imported Pygame modules (must be called before using Pygame features)
    WIDTH, HEIGHT = 800, 600
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("SpaceGame - Main Menu")

    clock = pygame.time.Clock()

    # fonts
    title_font = pygame.font.Font(None, 96)
    btn_font = pygame.font.Font(None, 48)

    # title
    title_surf = title_font.render("SpaceGame", True, (255,255,255))
    title_rect = title_surf.get_rect(center=(WIDTH//2, 150))

    # buttons
    btn_w, btn_h = 240, 64
    play_btn = Button((WIDTH//2 - btn_w//2, 300, btn_w, btn_h), "Play", btn_font)
    exit_btn = Button((WIDTH//2 - btn_w//2, 390, btn_w, btn_h), "Exit", btn_font)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if play_btn.handle_event(event):
                # run the user's game; return here after ESC or window close inside the game
                run_game()
                # Recreate title surface after returning (safe on some platforms)
                title_surf = title_font.render("SpaceGame", True, (255,255,255))

            if exit_btn.handle_event(event):
                running = False

        # Clear the entire screen and fill it with a dark background color
        screen.fill((15, 15, 20))

        # Draw small static “star” dots across the background for a simple space effect
        for x in range(40, WIDTH, 80):
            for y in range(60, HEIGHT, 120):

                # Draw a tiny dot (star) at position (x, y)
                pygame.draw.circle(screen, (60,60,80), (x, y), 1)

        screen.blit(title_surf, title_rect)
        play_btn.draw(screen)
        exit_btn.draw(screen)

        pygame.display.flip() # Update the entire screen to show everything drawn in this frame
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()