"""Series look: colours, font, cursor, intro / end card wording slots.

Everything that was hard-coded brand in the original generator is a field here.
A product's mold provides values (``demofoundry.json`` → ``Theme.from_dict``);
the defaults are a neutral dark look.
"""
from dataclasses import dataclass, field, fields


@dataclass
class Theme:
    # ground and text
    ground: str = '#09090b'
    ink: str = '#f2f4f7'
    ink_mute: str = '#858691'
    corner_ink: str = '#787884'
    badge_ink: str = '#9495a1'
    # accent (selection colour, end-card pill, intro glow)
    accent: str = '#7c5cff'
    accent_soft: str = '#c4b5fd'
    accent_glow_rgb: str = '140,94,255'
    # font: family name + optional local file (relative to the composition)
    font_family: str = 'Inter'
    font_src: str = ''
    font_stack: str = 'Inter, Arial, sans-serif'
    # cursor
    cursor_fill: str = '#fff'
    cursor_stroke: str = '#08080a'
    cursor_size: int = 96
    # series badge (top-left during the episode); empty = no badge
    badge_text: str = ''
    badge_logo: str = ''
    # end card
    logo: str = ''
    logo_alt: str = ''
    logo_width: int = 470
    site: str = ''
    powered_by: str = ''
    powered_icon: str = ''
    extra: dict = field(default_factory=dict)

    def font_face(self):
        """``@font-face`` rule for the theme font, or '' when it is a system font."""
        if not self.font_src:
            return ''
        return f'@font-face{{font-family:"{self.font_family}";src:url("{self.font_src}")}}'

    @classmethod
    def from_dict(cls, d):
        known = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in d.items() if k in known},
                   extra={k: v for k, v in d.items() if k not in known})
