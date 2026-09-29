import sys
from PIL import Image, ImageFilter, ImageChops

def whiten(src, dst, shadow=True, shadow_blur=10, shadow_alpha=140, shadow_offset=(0, 4)):
    im = Image.open(src).convert("RGBA")
    r, g, b, a = im.split()
    white = Image.new("RGBA", im.size, (255, 255, 255, 0))
    white.putalpha(a)

    if not shadow:
        white.save(dst)
        return

    # soft dark scrim/shadow behind the white glyph, offset slightly and blurred,
    # so the mark reads on busy footage instead of a flat CSS brightness hack.
    pad = shadow_blur * 3
    w, h = im.size
    canvas = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))

    shadow_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    shadow_alpha_img = Image.new("L", im.size, 0)
    shadow_alpha_img.paste(a, (0, 0))
    shadow_solid = Image.new("RGBA", im.size, (0, 0, 0, shadow_alpha))
    shadow_solid.putalpha(shadow_alpha_img.point(lambda v: int(v * shadow_alpha / 255)))
    shadow_layer.paste(shadow_solid, (pad + shadow_offset[0], pad + shadow_offset[1]), shadow_solid)
    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(shadow_blur))

    canvas = Image.alpha_composite(canvas, shadow_layer)
    canvas.paste(white, (pad, pad), white)
    canvas.save(dst)

if __name__ == "__main__":
    src, dst = sys.argv[1], sys.argv[2]
    shadow = "--no-shadow" not in sys.argv
    whiten(src, dst, shadow=shadow)
    print("wrote", dst)
