"""Low-resolution KardboardCode avatar rendering."""

from kardboard_vtuber.renderer.ps1_cardboard import (
    CardboardRendererConfig,
    PS1CardboardRenderer,
)
from kardboard_vtuber.renderer.textured_3d import (
    Textured3DCardboardRenderer,
    Textured3DRendererConfig,
)

__all__ = [
    "CardboardRendererConfig",
    "PS1CardboardRenderer",
    "Textured3DCardboardRenderer",
    "Textured3DRendererConfig",
]
