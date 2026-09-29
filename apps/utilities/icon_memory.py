"""Durable logo references kept beside uploaded media, independent of the DB."""
import json
import logging
import os
import tempfile
from pathlib import Path, PurePosixPath

from django.conf import settings

from .tool_icons import DEFAULT_SVGS

logger = logging.getLogger("dtest_nexus")


def remember_icon(key, image_name):
    if key not in DEFAULT_SVGS:
        return
    directory = Path(settings.MEDIA_ROOT) / "tools" / "icon-memory"
    directory.mkdir(parents=True, exist_ok=True)
    # One atomic file per tool prevents unrelated updates overwriting each other.
    fd, temporary = tempfile.mkstemp(dir=directory, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump({"version": 1, "image": image_name or None}, handle)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, directory / f"{key}.json")
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def remembered_icons():
    result = {}
    directory = Path(settings.MEDIA_ROOT) / "tools" / "icon-memory"
    for key in DEFAULT_SVGS:
        path = directory / f"{key}.json"
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
            name = record.get("image")
            if name is None:
                continue  # Explicit reset: never rediscover an old uploaded file.
            if (record.get("version") != 1 or not isinstance(name, str)
                    or not name.startswith("tools/icons/")
                    or ".." in PurePosixPath(name).parts or "\\" in name):
                raise ValueError("Invalid logo reference")
            result[key] = name
        except FileNotFoundError:
            continue
        except (OSError, ValueError, AttributeError):
            logger.warning("Cannot read saved Tools logo reference: %s", path)
    return result


def tool_icon_urls():
    from .models import ToolIcon

    names = remembered_icons()
    # Current database choices take precedence over the recovery references.
    names.update({icon.key: icon.image.name for icon in ToolIcon.objects.all()})
    storage = ToolIcon._meta.get_field("image").storage
    return {key: storage.url(name) for key, name in names.items()
            if key in DEFAULT_SVGS and name and storage.exists(name)}
