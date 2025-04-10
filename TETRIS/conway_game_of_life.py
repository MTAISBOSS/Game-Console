import time
import board
import displayio
import adafruit_ili9341
import busio
import random

# Release any previously used displays
displayio.release_displays()

# Define pins for the ILI9341 display
cs_pin = board.GP18
reset_pin = board.GP17
dc_pin = board.GP16
mosi_pin = board.GP3
clk_pin = board.GP2

# Initialize SPI
spi = busio.SPI(clock=clk_pin, MOSI=mosi_pin)

# Initialize the display bus
display_bus = displayio.FourWire(spi, command=dc_pin, chip_select=cs_pin, reset=reset_pin)

# Initialize the ILI9341 display (rotation set to 90 for vertical orientation)
display = adafruit_ili9341.ILI9341(display_bus, width=240, height=320, rotation=90)

# Create a display group
group = displayio.Group()
display.root_group = group

# Game of Life settings
GRID_WIDTH = 24
GRID_HEIGHT = 32
CELL_SIZE = 10  # Size of each cell in pixels

# Colors
DEAD_COLOR = 0x000000  # Black
ALIVE_COLOR = 0xFFFFFF  # Green

# Load a single color bitmap for alive cells
alive_bitmap = displayio.Bitmap(CELL_SIZE, CELL_SIZE, 1)
alive_palette = displayio.Palette(1)
alive_palette[0] = ALIVE_COLOR

class GameOfLife:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.grid = [[random.randint(0, 1) for _ in range(width)] for _ in range(height)]
        self.next_grid = [[0 for _ in range(width)] for _ in range(height)]

    def count_neighbors(self, x, y):
        """Count the number of alive neighbors for a cell at (x, y)."""
        neighbors = 0
        for i in range(-1, 2):
            for j in range(-1, 2):
                if i == 0 and j == 0:
                    continue  # Skip the cell itself
                nx, ny = x + i, y + j
                if 0 <= nx < self.width and 0 <= ny < self.height:
                    neighbors += self.grid[ny][nx]
        return neighbors

    def update(self):
        """Update the grid based on Conway's rules."""
        for y in range(self.height):
            for x in range(self.width):
                neighbors = self.count_neighbors(x, y)
                if self.grid[y][x]:  # Cell is alive
                    if neighbors < 2 or neighbors > 3:
                        self.next_grid[y][x] = 0  # Dies
                    else:
                        self.next_grid[y][x] = 1  # Survives
                else:  # Cell is dead
                    if neighbors == 3:
                        self.next_grid[y][x] = 1  # Becomes alive
                    else:
                        self.next_grid[y][x] = 0  # Stays dead
        # Swap grids
        self.grid, self.next_grid = self.next_grid, self.grid

    def draw(self, group):
        """Draw the current grid on the display."""
        # Clear the display group
        while len(group) > 0:
            group.pop()
        # Draw the grid
        for y in range(self.height):
            for x in range(self.width):
                if self.grid[y][x]:  # Cell is alive
                    tile = displayio.TileGrid(alive_bitmap, pixel_shader=alive_palette, x=x*CELL_SIZE, y=y*CELL_SIZE)
                    group.append(tile)

# Initialize the Game of Life
game = GameOfLife(GRID_WIDTH, GRID_HEIGHT)

# Main loop
while True:
    game.update()
    game.draw(group)
    #time.sleep(0.01)  # Adjust the speed of the simulation