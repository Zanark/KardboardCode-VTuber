"""Kraft-paper / forest-ink palettes shared by every Studio control state."""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication, QWidget


def titlebar(window: QWidget, dark: bool) -> str | None:
    if sys.platform != "win32" or QApplication.platformName() != "windows":
        return None
    import ctypes
    from ctypes import wintypes

    setter = ctypes.WinDLL("dwmapi").DwmSetWindowAttribute
    setter.argtypes = (wintypes.HWND, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD)
    setter.restype = ctypes.c_long
    colors = ((35, "#19332b" if dark else "#f3e7cc"),
              (36, "#fff4db" if dark else "#19332b"))
    failures = []
    for attribute, hex_color in colors:
        color = QColor(hex_color)
        value = wintypes.DWORD(color.red() | color.green() << 8 | color.blue() << 16)
        result = setter(int(window.winId()), attribute, ctypes.byref(value), ctypes.sizeof(value))
        if result:
            failures.append(str(result))
    return (
        "Windows custom title-bar colors are unavailable; using OS decoration. "
        + ", ".join(failures)
        if failures else None
    )


def stylesheet(dark: bool) -> str:
    bg, panel, field, text, muted, border, accent, on_accent, disabled, disabled_bg = (
        (
            "#11251f", "#19332b", "#10251e", "#fff4db", "#c2cfb9", "#5d7c68",
            "#9ce3bc", "#19332b", "#819385", "#24362c",
        )
        if dark else (
            "#f3e7cc", "#fff4db", "#fffaf0", "#19332b", "#4d6251", "#a68c64",
            "#276447", "#fff4db", "#786e5c", "#e2d5b9",
        )
    )
    palette = QPalette()
    for role, color in (
        (QPalette.ColorRole.Window, bg), (QPalette.ColorRole.WindowText, text),
        (QPalette.ColorRole.Base, field), (QPalette.ColorRole.AlternateBase, panel),
        (QPalette.ColorRole.Text, text), (QPalette.ColorRole.Button, panel),
        (QPalette.ColorRole.ButtonText, text), (QPalette.ColorRole.Highlight, accent),
        (QPalette.ColorRole.HighlightedText, on_accent),
        (QPalette.ColorRole.ToolTipBase, panel), (QPalette.ColorRole.ToolTipText, text),
    ):
        palette.setColor(role, QColor(color))
    for role in (
        QPalette.ColorRole.Text, QPalette.ColorRole.WindowText, QPalette.ColorRole.ButtonText,
    ):
        palette.setColor(QPalette.ColorGroup.Disabled, role, QColor(disabled))
    app = QApplication.instance()
    if app is not None:
        app.setPalette(palette)
    assets = Path(__file__).parent / "assets"
    tick = (assets / ("check-ink.svg" if dark else "check-cream.svg")).as_posix()
    disabled_tick = (assets / "check-cream.svg").as_posix()
    step_plus = (assets / "step-plus.svg").as_posix()
    step_minus = (assets / "step-minus.svg").as_posix()
    disabled_plus = (assets / f"step-plus-disabled-{'dark' if dark else 'light'}.svg").as_posix()
    disabled_minus = (assets / f"step-minus-disabled-{'dark' if dark else 'light'}.svg").as_posix()
    slider_accent = "#d5a568" if dark else accent
    return f"""
        QMainWindow, QDialog {{ background:{bg}; color:{text}; }}
        QWidget {{ color:{text}; font-family:'Segoe UI'; font-size:12px; }}
        QFrame#panel, QFrame#toolsPanel, QGroupBox {{
            background:{panel}; border:1px solid {border}; border-radius:9px;
        }}
        QGroupBox {{ margin-top:10px; padding:14px 10px 8px; }}
        QGroupBox::title {{ subcontrol-origin:margin; left:12px; padding:0 6px; }}
        QScrollArea, QScrollArea > QWidget > QWidget, QStackedWidget {{ background:{panel}; }}
        QLabel {{ background:transparent; }}
        QLabel#appTitle {{ font-size:17px; font-weight:700; }}
        QLabel#panelTitle {{ font-size:14px; font-weight:600; }}
        QLabel#eyebrow {{ color:{muted}; font-size:10px; font-weight:600; }}
        QLabel#hint, QLabel#sectionIntro {{ color:{muted}; font-size:11px; }}
        QLabel#status {{ background:{panel}; border-left:4px solid {accent};
            padding:5px 9px; font-weight:600; }}
        QLabel#sessionHint {{ color:{muted}; padding:4px 0; }}
        QLabel#sessionHint[busy="true"], QLabel#privateNotice {{
            color:{"#e8c58a" if dark else "#6c481e"}; padding:4px 0;
        }}
        QLabel#error, QLabel#warning {{ color:{text}; background:{panel};
            border:2px solid #d5a568; border-radius:6px; padding:10px; }}
        QLabel#lockBadge, QLabel#lockBadge:disabled {{
            color:{"#e8c58a" if dark else "#6c481e"}; font-size:10px; font-weight:700;
        }}
        QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QPlainTextEdit, QTextBrowser {{
            background:{field}; border:1px solid {border}; border-radius:5px;
            padding:6px; selection-background-color:{accent}; selection-color:{on_accent};
        }}
        QLineEdit:disabled, QComboBox:disabled, QSpinBox:disabled,
        QDoubleSpinBox:disabled {{ background:{disabled_bg}; color:{disabled}; }}
        QComboBox, QSpinBox, QDoubleSpinBox {{ min-height:20px; }}
        QSpinBox, QDoubleSpinBox {{ padding-right:26px; }}
        QSpinBox::up-button, QDoubleSpinBox::up-button {{
            subcontrol-origin:border; subcontrol-position:top right; width:22px;
            background:{"#d5a568" if dark else "#ead8b4"}; border-left:1px solid {border};
            border-bottom:1px solid {border}; border-top-right-radius:4px;
        }}
        QSpinBox::down-button, QDoubleSpinBox::down-button {{
            subcontrol-origin:border; subcontrol-position:bottom right; width:22px;
            background:{"#d5a568" if dark else "#ead8b4"}; border-left:1px solid {border};
            border-bottom-right-radius:4px;
        }}
        QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
        QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {{
            background:{"#e6bb86" if dark else "#d8bd8c"};
        }}
        QSpinBox::up-button:disabled, QDoubleSpinBox::up-button:disabled,
        QSpinBox::down-button:disabled, QDoubleSpinBox::down-button:disabled,
        QSpinBox::up-button:off, QDoubleSpinBox::up-button:off,
        QSpinBox::down-button:off, QDoubleSpinBox::down-button:off {{
            background:{disabled_bg}; color:{disabled};
        }}
        QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {{
            image:url("{step_plus}"); width:12px; height:12px;
        }}
        QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {{
            image:url("{step_minus}"); width:12px; height:12px;
        }}
        QSpinBox::up-arrow:disabled, QDoubleSpinBox::up-arrow:disabled,
        QSpinBox::up-arrow:off, QDoubleSpinBox::up-arrow:off {{
            image:url("{disabled_plus}");
        }}
        QSpinBox::down-arrow:disabled, QDoubleSpinBox::down-arrow:disabled,
        QSpinBox::down-arrow:off, QDoubleSpinBox::down-arrow:off {{
            image:url("{disabled_minus}");
        }}
        QComboBox QAbstractItemView {{
            background:{field}; color:{text}; selection-background-color:{accent};
            selection-color:{on_accent}; border:1px solid {border};
        }}
        QPushButton {{ background:{panel}; border:1px solid {border}; border-radius:6px;
            padding:7px 10px; font-weight:500; }}
        QPushButton:hover, QPushButton:focus {{ border:2px solid {accent}; }}
        QPushButton:checked, QPushButton#primary {{
            background:{accent}; color:{on_accent}; border-color:{accent}; font-weight:700;
        }}
        QPushButton:disabled {{
            background:{disabled_bg}; color:{disabled}; border-color:{border};
        }}
        QPushButton#primary:disabled {{
            background:{disabled_bg}; color:{disabled}; border-color:{border};
        }}
        QPushButton#stop {{ color:{"#ffc3a0" if dark else "#8c351c"}; border-color:#b27348; }}
        QToolButton {{ background:{panel}; border:1px solid {border}; border-radius:5px;
            padding:5px 8px; }}
        QToolButton:hover, QToolButton:focus {{ border:1px solid {accent}; }}
        QToolButton:checked {{ color:{accent}; }}
        QToolButton#sectionToggle {{
            text-align:left; border:0; border-bottom:1px solid {border};
            border-radius:0; padding:8px 2px; font-weight:600;
        }}
        QToolButton#sectionToggle:focus {{ border:1px solid {accent}; }}
        QPlainTextEdit#error {{ color:{text}; background:{panel}; border:2px solid #d5a568;
            font-family:'Segoe UI'; font-size:12px; }}
        QWidget:disabled {{ color:{disabled}; }}
        QCheckBox {{ spacing:9px; }}
        QCheckBox::indicator {{ width:19px; height:19px; border:2px solid {border};
            border-radius:3px; background:{field}; }}
        QCheckBox::indicator:checked {{ background:{accent}; border-color:{accent};
            image:url("{tick}"); }}
        QCheckBox::indicator:unchecked {{ image:none; }}
        QCheckBox::indicator:disabled {{ background:{disabled_bg}; border-color:{disabled}; }}
        QCheckBox::indicator:checked:disabled {{ background:#667260;
            image:url("{disabled_tick}"); }}
        QSlider::groove:horizontal {{ height:5px; background:{border}; border-radius:2px; }}
        QSlider::sub-page:horizontal {{ background:{slider_accent}; border-radius:2px; }}
        QSlider::handle:horizontal {{ width:15px; margin:-6px 0; background:{slider_accent};
            border:1px solid {border}; border-radius:7px; }}
        QSlider::sub-page:horizontal:disabled {{ background:{disabled}; }}
        QSlider::handle:horizontal:disabled {{ background:{disabled_bg}; border-color:{disabled}; }}
        QProgressBar {{ border:0; border-radius:4px; background:{border}; }}
        QProgressBar::chunk {{ background:{accent}; border-radius:4px; }}
        QTabWidget::pane {{ border:1px solid {border}; border-radius:6px; }}
        QTabBar::tab {{ background:{panel}; border:1px solid {border}; padding:7px 12px; }}
        QTabBar::tab:selected {{ border-bottom:3px solid {accent}; font-weight:600; }}
        QTabBar#workMode::tab {{ padding:7px 14px; font-size:12px; font-weight:600; }}
        QTabBar#workMode::tab:selected {{ background:{accent}; color:{on_accent}; }}
        QDockWidget {{ color:{muted}; }}
        QPlainTextEdit#console, QPlainTextEdit#command {{ font-family:Consolas; font-size:11px; }}
        QMenuBar, QMenu {{ background:{panel}; color:{text}; }}
        QMenu::item:selected {{ background:{accent}; color:{on_accent}; }}
        QToolTip {{ background:{panel}; color:{text}; border:1px solid {border}; }}
        QSplitter::handle {{ background:{border}; }}
    """
