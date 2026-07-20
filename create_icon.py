from PIL import Image, ImageDraw, ImageFont
import math

def create_app_icon():
    size = (256, 256)
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Rounded Square Background Gradient (Midnight Sapphire to Electric Cyan)
    margin = 8
    radius = 48
    
    # Draw base background circle/rounded rect with dark navy slate fill
    bg_color = (15, 23, 42, 255)
    draw.rounded_rectangle([margin, margin, size[0] - margin, size[1] - margin], radius=radius, fill=bg_color, outline=(56, 189, 248, 255), width=4)

    # Inner Glow Circle (Neon Teal / Cyan)
    center = (128, 128)
    for r in range(80, 70, -1):
        alpha = int(120 * ((80 - r) / 10))
        draw.ellipse([center[0] - r, center[1] - r, center[0] + r, center[1] + r], outline=(6, 182, 212, alpha), width=2)

    # Draw Headphones Arch (Cyber Blue)
    # Headband arc
    draw.arc([56, 50, 200, 190], start=180, end=0, fill=(56, 189, 248, 255), width=14)

    # Ear cups (Left & Right)
    draw.rounded_rectangle([48, 110, 72, 160], radius=8, fill=(16, 185, 129, 255), outline=(56, 189, 248, 255), width=3)
    draw.rounded_rectangle([184, 110, 208, 160], radius=8, fill=(16, 185, 129, 255), outline=(56, 189, 248, 255), width=3)

    # Draw Open Book Icon in Center
    # Left page
    draw.polygon([(84, 165), (124, 150), (124, 188), (84, 198)], fill=(248, 250, 252, 255))
    # Right page
    draw.polygon([(172, 165), (132, 150), (132, 188), (172, 198)], fill=(226, 232, 240, 255))
    # Spine line
    draw.line([(128, 148), (128, 192)], fill=(56, 189, 248, 255), width=3)

    # Sound Wave bars above book
    draw.line([(96, 135), (96, 120)], fill=(56, 189, 248, 255), width=4)
    draw.line([(112, 135), (112, 105)], fill=(16, 185, 129, 255), width=4)
    draw.line([(128, 135), (128, 95)], fill=(245, 158, 11, 255), width=4)
    draw.line([(144, 135), (144, 105)], fill=(16, 185, 129, 255), width=4)
    draw.line([(160, 135), (160, 120)], fill=(56, 189, 248, 255), width=4)

    # Save multi-resolution icon
    icon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    img.save("app_icon.ico", format="ICO", sizes=icon_sizes)
    img.save("app_icon.png", format="PNG")
    print("Created app_icon.ico successfully!")

if __name__ == "__main__":
    create_app_icon()
