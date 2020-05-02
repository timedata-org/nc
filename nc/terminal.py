from .colors import Colors
import contextlib
import functools
import subprocess

TERMINAL_ENVIRONMENT_VAR = '_NC_TERMINAL_COLOR_COUNT'
SIZES = 256, 16, 8


def context(fg=None, bg=None, print=print, count=None):
    return Context(count)(fg, bg, print)


@functools.lru_cache()
def color_count():
    cmd = 'tput', 'colors'
    try:
        count = int(subprocess.check_output(cmd, stderr=subprocess.STDOUT))
    except (FileNotFoundError, subprocess.CalledProcessError):
        return 0

    return next((s for s in SIZES if count >= s), 0)


@functools.lru_cache()
class Context:
    def __init__(self, count=None):
        self.count = color_count() if count is None else count
        if self.count:
            self.colors = Colors('terminal%s' % self.count)
            palette = self.colors._palettes[0]
            codes = palette['CODES']
            self.CODES = {self.colors[k]: v for k, v in codes.items()}
            self.fg = palette['fg']
            self.bg = palette['bg']

    def __bool__(self):
        return bool(self.count)

    @contextlib.contextmanager
    def __call__(self, fg=None, bg=None, print=print):
        def print_codes(*codes):
            result = '\x1b[%sm' % ';'.join(str(c) for c in codes)
            print(result, end='')

        def color_codes(color, coder):
            if not color:
                return ()
            closest = self.colors.closest(color)
            return coder(self.CODES[closest])

        if self and (fg or bg):
            codes = color_codes(fg, self.fg) + color_codes(bg, self.bg)
            print_codes(*codes)
            yield
            print_codes()

        else:
            yield
