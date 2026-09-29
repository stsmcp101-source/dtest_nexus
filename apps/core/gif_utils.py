"""
Slows down (or speeds up) animated GIFs used as homepage menu-strip
images, so an administrator can tune playback speed from the Home
Appearance settings page without re-exporting the GIF in external
software. A browser has no native playback-rate control for an
animated <img>/background-image GIF, so the only way to change how
fast one plays is to rewrite each frame's own duration and re-encode —
that's all this module does. Pure functions, no request/model
coupling — apps.core.views wires this to ModuleDefinition.
"""
import io

from django.core.files.base import ContentFile
from PIL import Image, ImageSequence

MIN_FRAME_DURATION_MS = 20  # browsers clamp anything lower to ~100ms anyway


def build_speed_adjusted_gif(fileobj, speed_multiplier):
    """Re-encodes an animated GIF with every frame's duration multiplied
    by speed_multiplier (>1 slows playback down, <1 speeds it up).
    Returns an io.BytesIO on success, or None when there's nothing to
    adjust (source isn't an animated GIF, or speed_multiplier is ~1)."""
    if abs(speed_multiplier - 1.0) < 1e-6:
        return None

    fileobj.seek(0)
    try:
        img = Image.open(fileobj)
    except Exception:
        return None
    if img.format != "GIF" or not getattr(img, "is_animated", False):
        return None

    frames = []
    durations = []
    for frame in ImageSequence.Iterator(img):
        frames.append(frame.copy())
        base_duration = frame.info.get("duration", 100)
        durations.append(max(MIN_FRAME_DURATION_MS, round(base_duration * speed_multiplier)))

    output = io.BytesIO()
    frames[0].save(
        output, format="GIF", save_all=True, append_images=frames[1:],
        duration=durations, loop=img.info.get("loop", 0), disposal=2,
    )
    output.seek(0)
    return output


def refresh_module_gif_speed(module):
    """(Re)generates ModuleDefinition.background_image_processed from
    the current background_image + background_image_speed. Always
    derives from the pristine original upload (background_image is
    never overwritten), so repeatedly tweaking the speed never
    compounds. Call after any save that could have changed either
    field. No-op fields (static image, or speed == 1) leave
    background_image_processed empty so templates fall back to
    background_image directly."""
    if module.background_image_processed:
        module.background_image_processed.delete(save=False)

    if module.background_image:
        module.background_image.open("rb")
        try:
            adjusted = build_speed_adjusted_gif(module.background_image, module.background_image_speed)
        finally:
            module.background_image.close()
        if adjusted is not None:
            filename = module.background_image.name.rsplit("/", 1)[-1]
            module.background_image_processed.save(filename, ContentFile(adjusted.read()), save=False)

    module.save(update_fields=["background_image_processed"])
