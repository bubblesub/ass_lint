from collections import defaultdict
from functools import cache
from pathlib import Path
from typing import Optional

import ass_tag_parser
import fontTools.ttLib as font_tools
from ass_parser import AssFile

from .base import BaseCheck, Information, Violation

TT_NAME_ID_FONT_FAMILY = 1
TT_NAME_ID_FULL_NAME = 4
TT_NAME_ID_TYPOGRAPHIC_FAMILY = 16
TT_PLATFORM_MICROSOFT = 3


class FontInfo:
    def __init__(self, font_path):
        font = font_tools.TTFont(font_path)

        self.names = []
        self.is_bold = bool(font["OS/2"].fsSelection & (1 << 5))
        self.is_italic = bool(font["OS/2"].fsSelection & 1)
        self.glyphs = set(
            chr(y[0]) for x in font["cmap"].tables for y in x.cmap.items()
        )

        for record in font["name"].names:
            if record.platformID != TT_PLATFORM_MICROSOFT:
                continue

            if record.nameID not in {
                TT_NAME_ID_FONT_FAMILY,
                TT_NAME_ID_FULL_NAME,
                TT_NAME_ID_TYPOGRAPHIC_FAMILY,
            }:
                continue

            self.names.append(record.string.decode("utf-16-be"))


def get_used_font_styles(
    ass_file: AssFile,
) -> dict[tuple[str, bool, bool], set[str]]:
    results = defaultdict(set)

    styles = {style.name: style for style in ass_file.styles}
    for event in ass_file.events:
        if event.is_comment:
            continue

        style = styles.get(event.style_name)
        if not style:
            continue

        family = style.font_name
        is_bold = style.bold
        is_italic = style.italic

        try:
            ass_line = ass_tag_parser.parse_ass(event.text)
        except ass_tag_parser.ParseError:
            # ASS parsing errors are handled elsewhere
            continue

        for item in ass_line:
            if isinstance(item, ass_tag_parser.AssTagBold):
                is_bold = (
                    item.enabled if item.weight is None else item.weight > 100
                )
            elif isinstance(item, ass_tag_parser.AssTagItalic):
                is_italic = item.enabled
            elif isinstance(item, ass_tag_parser.AssTagFontName):
                family = (
                    item.name if item.name else styles[event.style].font_name
                )
            elif isinstance(item, ass_tag_parser.AssText):
                for glyph in item.text:
                    results[(family, is_bold, is_italic)].add(glyph)

    return results


def get_font_description(
    font_family: str, is_bold: bool, is_italic: bool
) -> str:
    attrs = []
    if is_bold:
        attrs.append("bold")
    if is_italic:
        attrs.append("italic")
    if attrs:
        return f"{font_family} ({', '.join(attrs)})"
    return font_family


@cache
def get_fonts(fonts_dir: Path) -> dict[Path, FontInfo]:
    ret: dict[Path, FontInfo] = {}
    for path in fonts_dir.iterdir():
        if path.is_file():
            try:
                ret[path] = FontInfo(path)
            except font_tools.TTLibError:
                pass
    return ret


def locate_font(
    fonts: dict[Path, FontInfo], family: str, is_bold: bool, is_italic: bool
) -> Optional[Path]:
    candidates = []
    for font_path, font in fonts.items():
        if family.lower() in [n.lower() for n in font.names]:
            weight = (font.is_bold == is_bold) + (font.is_italic == is_italic)
            candidates.append((weight, font_path, font))
    candidates.sort(key=lambda i: -i[0])
    if not candidates:
        return None
    return candidates[0]


class CheckFonts(BaseCheck):
    async def run(self) -> None:
        results = ["Fonts summary:"]

        font_styles = get_used_font_styles(self.ctx.ass_file)
        fonts = get_fonts(self.ctx.fonts_dir)
        for font_specs, glyphs in font_styles.items():
            font_family, is_bold, is_italic = font_specs
            results.append(
                f"– {get_font_description(*font_specs)}, {len(glyphs)} glyphs"
            )

            result = locate_font(fonts, font_family, is_bold, is_italic)
            if not result:
                yield Violation(
                    f"{get_font_description(*font_specs)}: font file not found"
                )
                continue

            _weight, _font_path, font = result
            missing_glyphs = set()
            for glyph in glyphs:
                if glyph not in font.glyphs:
                    missing_glyphs.add(glyph)

            if missing_glyphs:
                yield Violation(
                    f"{get_font_description(*font_specs)}: missing glyphs ("
                    f'{"".join(missing_glyphs)}'
                )

        yield Information("\n".join(results))
