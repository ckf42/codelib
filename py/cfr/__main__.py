import sys

from . import App

if __name__ == '__main__':
    App(code=sys.argv[1], reportProress=True).run(fastDraw=True)
