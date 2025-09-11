"""
Enhanced Resource Helper - Gobioeng HALog
Provides robust resource path resolution that works in development and PyInstaller environments
Date: 2025-08-22 16:47:11 UTC
Developer: Tanmay Pandey
Company: gobioeng.com
"""

import sys
import os
from pathlib import Path
from PyQt5.QtGui import (
    QIcon,
    QPixmap,
    QImage,
    QPainter,
    QColor,
    QBrush,
    QLinearGradient,
    QRadialGradient,
    QFont,
    QPen,
)
from PyQt5.QtCore import QSize, Qt, QRect


def resource_path(relative_path):
    """
    Failsafe way to find assets in dev, PyInstaller (internal/onedir), and any folder structure.
    Usage: resource_path('halogo.ico')
    Developer: Tanmay Pandey
    """
    # Check PyInstaller _MEIPASS
    if hasattr(sys, "_MEIPASS"):
        # Try assets inside _MEIPASS (PyInstaller 6+)
        candidate = os.path.join(
            sys._MEIPASS, "assets", os.path.basename(relative_path)
        )
        if os.path.exists(candidate):
            return candidate
        # Try assets one level up (for some internal layouts)
        parent_assets = os.path.join(
            os.path.dirname(sys._MEIPASS), "assets", os.path.basename(relative_path)
        )
        if os.path.exists(parent_assets):
            return parent_assets
        # Try file directly in _MEIPASS
        direct_file = os.path.join(sys._MEIPASS, os.path.basename(relative_path))
        if os.path.exists(direct_file):
            return direct_file

    # Development (source) - assets folder next to script
    dev_assets = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "assets",
        os.path.basename(relative_path),
    )
    if os.path.exists(dev_assets):
        return dev_assets

    # Try cwd/assets
    cwd_assets = os.path.join(os.getcwd(), "assets", os.path.basename(relative_path))
    if os.path.exists(cwd_assets):
        return cwd_assets

    # Try just cwd
    direct_cwd = os.path.join(os.getcwd(), os.path.basename(relative_path))
    if os.path.exists(direct_cwd):
        return direct_cwd

    # Fallback: return as-is (will likely fail, but avoids crash)
    return relative_path


def load_splash_icon(size=120):
    """
    Load icon specifically for splash screen with maximum quality preservation
    Priority: High-res PNG > Low-res PNG > ICO > Generated fallback
    Developer: Tanmay Pandey - gobioeng.com
    """
    print(f"Loading splash icon with size: {size}")

    # Try PNG files first (highest quality) - prioritize by resolution
    png_files = ["halogo_256.png", "halogo_100.png", "halogo.png"]

    for png_name in png_files:
        png_path = resource_path(png_name)
        print(f"Trying PNG: {png_path}")
        if os.path.exists(png_path):
            pixmap = QPixmap(png_path)
            if not pixmap.isNull():
                print(
                    f"Successfully loaded PNG: {png_path} (original size: {pixmap.size()})"
                )
                # Apply contrast enhancement
                enhanced_pixmap = enhance_icon_contrast(pixmap)
                return enhanced_pixmap.scaled(
                    size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation
                )

    # Try ICO files with size preference
    ico_files = ["halogo_256.ico", "halogo_100.ico", "halogo.ico"]

    for ico_name in ico_files:
        ico_path = resource_path(ico_name)
        print(f"Trying ICO: {ico_path}")
        if os.path.exists(ico_path):
            # Load ICO with specific size preference
            icon = QIcon(ico_path)
            if not icon.isNull():
                # Get the largest available size
                available_sizes = icon.availableSizes()
                if available_sizes:
                    largest_size = max(
                        available_sizes, key=lambda s: s.width() * s.height()
                    )
                    pixmap = icon.pixmap(largest_size)
                    print(f"ICO loaded with size: {largest_size}")
                else:
                    pixmap = icon.pixmap(size, size)

                if not pixmap.isNull():
                    print(
                        f"Successfully loaded ICO: {ico_path} (size: {pixmap.size()})"
                    )
                    # Apply contrast enhancement
                    enhanced_pixmap = enhance_icon_contrast(pixmap)
                    return enhanced_pixmap.scaled(
                        size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation
                    )

    # If both fail, try direct loading
    print("Trying direct icon loading...")
    direct_icon = load_direct_icon(size)
    if direct_icon and not direct_icon.isNull():
        return direct_icon

    # Generate high-quality fallback if no files found
    print("No icon files found, generating high-quality fallback")
    return generate_icon(size, high_quality=True)


def enhance_icon_contrast(pixmap):
    """
    Enhance icon contrast and visibility for splash screen
    Advanced image processing by Tanmay Pandey
    """
    if pixmap.isNull():
        return pixmap

    print("Enhancing icon contrast...")

    # Convert to image for pixel manipulation
    image = pixmap.toImage()

    # Create enhanced image with higher quality format
    enhanced = QImage(image.size(), QImage.Format_ARGB32_Premultiplied)
    enhanced.fill(Qt.transparent)

    # Apply contrast and saturation enhancement
    for y in range(image.height()):
        for x in range(image.width()):
            color = QColor(image.pixel(x, y))

            # Skip fully transparent pixels
            if color.alpha() < 10:
                enhanced.setPixelColor(x, y, color)
                continue

            # Get HSV values for better control
            h, s, v, a = color.getHsvF()

            # Enhance saturation significantly (make colors more vibrant)
            s = min(1.0, s * 1.8)

            # Enhance contrast: make dark colors darker, bright colors brighter
            if v < 0.2:
                v = max(0.0, v * 0.6)  # Make very dark colors darker
            elif v < 0.4:
                v = max(0.0, v * 0.8)  # Make dark colors darker
            elif v > 0.8:
                v = min(1.0, v * 1.3)  # Make bright colors brighter
            elif v > 0.6:
                v = min(1.0, v * 1.2)  # Make fairly bright colors brighter
            else:
                v = min(1.0, v * 1.1)  # Slightly enhance mid-tones

            # Ensure strong alpha (reduce transparency)
            a = min(1.0, a * 1.4)

            # Apply enhanced color
            color.setHsvF(h, s, v, a)
            enhanced.setPixelColor(x, y, color)

    print("Icon contrast enhancement completed")
    return QPixmap.fromImage(enhanced)


def load_direct_icon(size=120):
    """
    Direct loading of icon files with comprehensive error handling
    Robust file handling by Tanmay Pandey
    """
    print("Attempting direct icon loading...")

    # List of possible icon files in order of preference
    icon_files = [
        "halogo_256.png",
        "halogo_256.ico",
        "halogo_100.png",
        "halogo_100.ico",
        "halogo.png",
        "halogo.ico",
    ]

    for icon_file in icon_files:
        full_path = resource_path(icon_file)
        print(f"Trying direct load: {full_path}")

        if os.path.exists(full_path):
            print(f"File exists: {full_path}")

            try:
                if icon_file.endswith(".png"):
                    pixmap = QPixmap(full_path)
                else:  # ICO file
                    # For ICO files, try to get the largest size
                    icon = QIcon(full_path)
                    available_sizes = icon.availableSizes()
                    if available_sizes:
                        largest_size = max(available_sizes, key=lambda s: s.width())
                        pixmap = icon.pixmap(largest_size)
                    else:
                        pixmap = QPixmap(full_path)

                if not pixmap.isNull():
                    print(f"Successfully loaded: {full_path} (size: {pixmap.size()})")
                    # Apply enhancement and scale
                    enhanced = enhance_icon_contrast(pixmap)
                    return enhanced.scaled(
                        size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation
                    )
                else:
                    print(f"Failed to load pixmap from: {full_path}")
            except Exception as e:
                print(f"Error loading {full_path}: {e}")
        else:
            print(f"File not found: {full_path}")

    print("Direct icon loading failed")
    return None


def generate_icon(size=128, color="#1565c0", text="HA", high_quality=True):
    """
    Generate a high-visibility fallback icon with maximum contrast
    Professional icon generation by Tanmay Pandey - gobioeng.com
    """
    print(f"Generating fallback icon with size: {size}")

    # Create a blank pixmap with 4x size for even higher resolution
    actual_size = size * 4 if high_quality else size
    pixmap = QPixmap(actual_size, actual_size)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing, True)
    painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
    painter.setRenderHint(QPainter.TextAntialiasing, True)
    painter.setRenderHint(QPainter.HighQualityAntialiasing, True)

    # Draw vibrant blue background with better contrast
    painter.setBrush(QColor("#0d47a1"))  # Deep blue background
    painter.setPen(Qt.NoPen)
    painter.drawEllipse(0, 0, actual_size, actual_size)

    # Add metallic gradient overlay for professional look
    gradient = QRadialGradient(actual_size / 3, actual_size / 3, actual_size)
    gradient.setColorAt(0, QColor(255, 255, 255, 100))  # Bright white highlight
    gradient.setColorAt(0.4, QColor(30, 136, 229, 140))  # Mid-blue
    gradient.setColorAt(0.8, QColor(13, 71, 161, 200))  # Deep blue
    gradient.setColorAt(1, QColor(8, 40, 100, 255))  # Very deep blue edge

    painter.setBrush(QBrush(gradient))
    painter.drawEllipse(0, 0, actual_size, actual_size)

    # Add a strong border for definition
    border_width = actual_size // 25
    painter.setPen(QPen(QColor(255, 255, 255, 120), border_width))
    painter.drawEllipse(
        border_width // 2,
        border_width // 2,
        actual_size - border_width,
        actual_size - border_width,
    )

    # Draw text with maximum contrast and multiple shadows
    font = painter.font()
    font.setPointSize(actual_size // 2.2)  # Slightly larger text
    font.setBold(True)
    font.setWeight(QFont.Black)  # Heaviest weight
    font.setFamily("Arial Black")
    painter.setFont(font)

    # Add multiple drop shadows for depth and contrast
    shadow_colors = [
        (QColor(0, 0, 0, 80), 6),  # Dark shadow, far offset
        (QColor(0, 0, 0, 60), 4),  # Medium shadow
        (QColor(0, 0, 0, 40), 2),  # Close shadow
    ]

    for shadow_color, offset in shadow_colors:
        painter.setPen(shadow_color)
        text_rect = QRect(offset, offset, actual_size, actual_size)
        painter.drawText(text_rect, Qt.AlignCenter, text)

    # Draw main text - PURE WHITE with maximum contrast
    painter.setPen(QColor(255, 255, 255, 255))
    text_rect = QRect(0, 0, actual_size, actual_size)
    painter.drawText(text_rect, Qt.AlignCenter, text)

    # Add text outline for even better definition
    outline_pen = QPen(QColor(255, 255, 255, 180))
    outline_pen.setWidth(actual_size // 60)
    painter.setPen(outline_pen)
    painter.drawText(text_rect, Qt.AlignCenter, text)

    # Add top shine effect
    shine_gradient = QLinearGradient(0, 0, 0, actual_size // 3)
    shine_gradient.setColorAt(0, QColor(255, 255, 255, 120))
    shine_gradient.setColorAt(1, QColor(255, 255, 255, 0))

    painter.setBrush(QBrush(shine_gradient))
    painter.setPen(Qt.NoPen)
    painter.drawEllipse(
        actual_size // 6, actual_size // 10, actual_size * 2 // 3, actual_size // 3
    )

    painter.end()

    # Scale down to requested size if needed (maintains high quality)
    if high_quality and size != actual_size:
        pixmap = pixmap.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)

    print("Fallback icon generation completed")
    return pixmap


def get_app_icon():
    """
    Get application icon with fallback generation and enhanced visibility
    Icon management system by Tanmay Pandey
    """
    print("Loading application icon...")

    # Try high-resolution files first
    for icon_file in [
        "halogo_256.png",
        "halogo_256.ico",
        "halogo.png",
        "halogo.ico",
    ]:
        icon_path = resource_path(icon_file)
        if os.path.exists(icon_path):
            try:
                if icon_file.endswith(".png"):
                    img = QImage(icon_path)
                else:
                    # For ICO, load as pixmap first
                    pixmap = QPixmap(icon_path)
                    img = pixmap.toImage()

                if not img.isNull():
                    # Apply enhancement
                    enhanced_img = enhance_icon_image(img)

                    # Create icon with multiple sizes
                    icon = QIcon()
                    for size in [16, 32, 64, 128, 256]:
                        enhanced_pixmap = QPixmap.fromImage(
                            enhanced_img.scaled(
                                size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation
                            )
                        )
                        icon.addPixmap(enhanced_pixmap)
                    return icon
            except Exception as e:
                print(f"Error loading app icon from {icon_file}: {e}")

    # Generate high visibility icon as fallback
    print("Creating high-visibility app icon")
    icon = QIcon()
    for size in [16, 32, 64, 128, 256]:
        icon.addPixmap(generate_icon(size, high_quality=True), QIcon.Normal, QIcon.Off)

    return icon


def enhance_icon_image(img):
    """
    Apply enhancement to existing icon to improve visibility
    Image enhancement algorithm by Tanmay Pandey
    """
    if img.isNull():
        return img

    # Create enhanced copy of the image
    enhanced = QImage(img.size(), QImage.Format_ARGB32_Premultiplied)
    enhanced.fill(Qt.transparent)

    # Apply the same enhancement as splash icon
    for y in range(img.height()):
        for x in range(img.width()):
            color = QColor(img.pixel(x, y))

            # Skip transparent pixels
            if color.alpha() < 5:
                enhanced.setPixelColor(x, y, color)
                continue

            # Enhance color
            h, s, v, a = color.getHsvF()

            # Boost saturation significantly
            s = min(1.0, s * 1.6)

            # Boost contrast
            if v < 0.3:
                v = min(1.0, v * 0.8)
            else:
                v = max(0.3, min(1.0, v * 1.2))

            # Ensure alpha is strong
            a = min(1.0, a * 1.3)

            # Apply enhanced color
            color.setHsvF(h, s, v, a)
            enhanced.setPixelColor(x, y, color)

    return enhanced


def ensure_app_icon():
    """
    Ensure the application icon exists, generating if necessary
    Developed by Tanmay Pandey - gobioeng.com
    """
    icon_files = ["halogo_256.png", "halogo.png", "halogo.ico"]

    for icon_file in icon_files:
        icon_path = Path(resource_path(icon_file))
        if icon_path.exists():
            return str(icon_path)

    # Generate fallback
    assets_dir = Path(__file__).parent / "assets"
    assets_dir.mkdir(exist_ok=True)

    fallback_path = assets_dir / "halogo_generated.png"
    if not fallback_path.exists():
        generate_icon(256, high_quality=True).save(str(fallback_path))
        print(f"Created high-visibility fallback icon: {fallback_path}")

    return str(fallback_path)
