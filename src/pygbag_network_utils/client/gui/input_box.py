import pygame

from .consts import BLACK, DARK_BLUE, LIGHT_GRAY, WHITE, FONT_SMALL


class InputBox:
    def __init__(self, x, y, width, height, text="", on_enter_callback=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = BLACK
        self.text = text
        self.txt_surface = FONT_SMALL.render(text, True, self.color)
        self.active = False
        self.on_enter_callback = on_enter_callback

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            # If the user clicked on the input_box rect.
            if self.rect.collidepoint(event.pos):
                # Toggle the active variable.
                self.active = not self.active
            else:
                self.active = False
            # Change the current color of the input box.
            self.color = DARK_BLUE if self.active else BLACK
        if event.type == pygame.KEYDOWN:
            if self.active:
                if event.key == pygame.K_RETURN:
                    if self.on_enter_callback:
                        self.on_enter_callback()
                    self.text = ""
                elif event.key == pygame.K_ESCAPE:
                    self.text = ""
                    # self.active = False
                elif event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                else:
                    self.text += event.unicode
                # Re-render the text.
                self.txt_surface = FONT_SMALL.render(
                    self.text,
                    True,
                    self.color,
                )

    def draw(self, screen):
        pygame.draw.rect(screen, LIGHT_GRAY if self.active else WHITE, self.rect)
        # Blit the text.
        screen.blit(self.txt_surface, (self.rect.x + 5, self.rect.y + 5))
        # Blit the rect.
        pygame.draw.rect(screen, self.color, self.rect, 2)

    def set_on_enter_callback(self, callback):
        self.on_enter_callback = callback
