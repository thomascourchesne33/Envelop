"""Convert envelop_logo.svg → icon.ico using PyQt6 to render the SVG."""
import sys
import os

svg_path = os.path.join(os.path.dirname(__file__), "envelop_logo.svg")
ico_path = os.path.join(os.path.dirname(__file__), "icon.ico")

from PyQt6.QtWidgets import QApplication
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtGui import QPixmap, QPainter, QImage
from PyQt6.QtCore import Qt, QSize

app = QApplication(sys.argv)

sizes = [16, 24, 32, 48, 64, 128, 256]
pil_images = []

from PIL import Image
import io

for size in sizes:
    img = QImage(size, size, QImage.Format.Format_ARGB32)
    img.fill(0)  # transparent
    painter = QPainter(img)
    renderer = QSvgRenderer(svg_path)
    renderer.render(painter)
    painter.end()

    # Convert QImage to PIL
    buf = img.bits().asarray(size * size * 4)
    pil_img = Image.frombytes("RGBA", (size, size), bytes(buf), "raw", "BGRA")
    pil_images.append(pil_img)

# Save as ICO with all sizes
pil_images[0].save(
    ico_path,
    format="ICO",
    sizes=[(s, s) for s in sizes],
    append_images=pil_images[1:],
)
print(f"Saved: {ico_path}")
app.quit()
