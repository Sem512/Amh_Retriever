# Image cleanup and finding text on signs (Kibreab)

Delivers `clean(photo, mode)`, `find_lines(image)` and `crop_line(image, corners)`. Their exact inputs
and outputs are in [`ARCHITECTURE.md`](../ARCHITECTURE.md) section 3, and the per-mode behaviour is in
section 2.

The one rule everything downstream depends on: **the image `clean()` returns is the image the viewer
shows, and every box (OCR lines, sign lines, highlights) is in its pixel coordinates.** Its long side
must be at most 2500 px.

Nothing has been built here yet.
