from enum import IntEnum as _Enum
import typing as _tp

_P = _tp.ParamSpec('P')

_ESCAPE: str = '\x1b'
_CSI: str = _ESCAPE + '['

class EraseDisplayMode(_Enum):
    TILL_END = 0
    TILL_BEGIN = 1
    ALL = 2
    ALL_WITH_BUFFER = 3

class EraseLineMode(_Enum):
    TILL_END = 0
    TILL_BEGIN = 1
    ALL = 2

class Color(_Enum):
    BLACK = 30
    RED = 31
    GREEN = 32
    YELLOW = 33
    BLUE = 34
    MAGENTA = 35
    CYNA = 36
    WHITE = 37
    BLIGHT_BLACK = 90
    BLIGHT_RED = 91
    BLIGHT_GREEN = 92
    BLIGHT_YELLOW = 93
    BLIGHT_BLUE = 94
    BLIGHT_MAGENTA = 95
    BLIGHT_CYNA = 96
    BLIGHT_WHITE = 97


def curser_up(n: int = 1) -> str:
    return f'{_CSI}{n}A'

def curser_down(n: int = 1) -> str:
    return f'{_CSI}{n}B'

def curser_right(n: int = 1) -> str:
    return f'{_CSI}{n}C'

def curser_left(n: int = 1) -> str:
    return f'{_CSI}{n}D'

def curser_next_line_begin(n: int = 1) -> str:
    return f'{_CSI}{n}E'

def curser_prev_line_begin(n: int = 1) -> str:
    return f'{_CSI}{n}F'

def curser_col(n: int = 1) -> str:
    return f'{_CSI}{n}G'

def curser_abs_pos(x: int = 1, y: int = 1) -> str:
    return f'{_CSI}{x};{y}H'

def curser_erase_display(
        eraseMode: EraseDisplayMode = EraseDisplayMode.ALL
        ) -> str:
    return f'{_CSI}{eraseMode.value}J'

def curser_erase_line(
        eraseMode: EraseLineMode = EraseLineMode.TILL_END
        ) -> str:
    return f'{_CSI}{eraseMode.value}K'

def curser_scroll_up(n: int = 1) -> str:
    return f'{_CSI}{n}S'

def curser_scroll_down(n: int = 1) -> str:
    return f'{_CSI}{n}T'

def _applier(
        func: _tp.Callable[_P, str]
        ) -> _tp.Callable[_P, _tp.Callable[[str], str]]:
    def f(*args: _P.args,
          **kwargs: _P.kwargs) -> _tp.Callable[[str], str]:
        onMod: str = func(*args, **kwargs, on=True)
        offMod: str = func(*args, **kwargs, on=False)
        def g(text: str) -> str:
            return onMod + text + offMod
        g.modifier = onMod
        return g
    return f

text_reset: str = _CSI + '0m'

@_applier
def text_bold(on: bool = True) -> str:
    return _CSI + ('1' if on else '22') + 'm'

@_applier
def text_faint(on: bool = True) -> str:
    return _CSI + ('2' if on else '22') + 'm'

@_applier
def text_italic(on: bool = True) -> str:
    return _CSI + ('2' if not on else '') + '3m'

@_applier
def text_underline(double: bool = False, on: bool = True) -> str:
    if not on:
        return _CSI + '24m'
    return _CSI + ('21' if double else '4') + 'm'

@_applier
def text_underline_double(on: bool = True) -> str:
    return text_underline(double=True, on=on)

@_applier
def text_overline(on: bool = True) -> str:
    return _CSI + '5' + ('3' if on else '5') + 'm'

@_applier
def text_blink(on: bool = True) -> str:
    return _CSI + ('2' if not on else '') + '5m'

@_applier
def text_invert(on: bool = True) -> str:
    return _CSI + ('2' if not on else '') + '7m'

@_applier
def text_conceal(on: bool = True) -> str:
    return _CSI + ('2' if not on else '') + '8m'

@_applier
def text_crossout(on: bool = True) -> str:
    return _CSI + ('2' if not on else '') + '9m'

text_reset_fg: str = _CSI + '39m'

@_applier
def text_set_fg(color: Color, on: bool = True) -> str:
    if not on:
        return text_reset_fg
    return _CSI + f'{color.value}m'

@_applier
def text_set_fg_8bit(code: int, on: bool = True) -> str:
    if not on:
        return text_reset_fg
    assert 0 <= code < 256
    return _CSI + f'38;5;{code}m'

@_applier
def text_set_fg_rgb(r: int, g: int, b: int, on: bool = True) -> str:
    if not on:
        return text_reset_fg
    assert r >= 0
    assert g >= 0
    assert b >= 0
    return _CSI + f'38;2;{r};{g};{b}m'

text_reset_bg: str = _CSI + '49m'

@_applier
def text_set_bg(color: Color, on: bool = True) -> str:
    if not on:
        return text_reset_bg
    return _CSI + f'{color.value + 10}m'

@_applier
def text_set_bg_8bit(code: int, on: bool = True) -> str:
    if not on:
        return text_reset_bg
    assert 0 <= code < 256
    return _CSI + f'48;5;{code}m'

@_applier
def text_set_bg_rgb(r: int, g: int, b: int, on: bool = True) -> str:
    if not on:
        return text_reset_bg
    assert r >= 0
    assert g >= 0
    assert b >= 0
    return _CSI + f'48;2;{r};{g};{b}m'

def textop_wrap(ops: _tp.Sequence[_tp.Callable[[str], str]],
                text: str) -> str:
    for op in ops[::-1]:
        text = op(text)
    return text

