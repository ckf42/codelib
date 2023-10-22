import contextlib
import enum
from functools import cached_property

with contextlib.redirect_stdout(None):
    import pygame as pg


class Color(enum.Enum):
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    BLUE = (0, 0, 255)
    GREEN = (0, 255, 0)
    CYAN = (0, 255, 255)
    RED = (255, 0, 0)
    MAGENTA = (255, 0, 255)
    YELLOW = (255, 255, 0)


colorPalette: tuple[Color, ...] = (
    Color.WHITE, Color.BLACK, Color.BLUE, Color.GREEN,
    Color.CYAN, Color.RED, Color.MAGENTA, Color.YELLOW
)

dirPalette: tuple[tuple[int, int], ...] = (
    (0, 1), (1, 1), (1, 0), (1, -1),
    (0, -1), (-1, -1), (-1, 0), (-1, 1)
)


class CFR:
    def __init__(self, code: str, reportProress: bool) -> None:
        """
        setting reportProress True may slow down process on long code
        """
        self.code: str = ''.join(c for c in code.upper() if c in 'CFR[]')
        self.isValid: bool = True
        self.isReportProgress: bool = reportProress
        if len(self.code) > 256:
            print("Code too long")
            self.isValid = False
        if not self.verify():
            print("Bracket mismatch")
            self.isValid = False
        self.x: int = 127
        self.y: int = 127
        self.dirPtr: int = 0
        self.colorPtr: int = 0
        self.codePtr: int = 0
        self.codeSize: int = len(self.code)
        self.blockStack: list[int] = list()
        self.isRunning: bool = True
        self.stepCount: int = 0

    def verify(self, strict: bool = False) -> bool:
        """
        strict checks if all opening brackets are closed
        [Spec](https://github.com/susam/cfr#code-normalisation-and-validation)
            does not require them to be closed
        """
        counter = 0
        for c in self.code:
            if c == '[':
                counter += 1
            elif c == ']':
                if counter == 0:
                    return False
                counter -= 1
        return not strict or counter == 0

    @cached_property
    def codeTotalLen(self) -> int:
        if not self.isValid:
            return 0
        stack: list[int] = [0]
        for c in self.code:
            match c:
                case '[':
                    stack.append(0)
                case ']':
                    stacktop = stack.pop()
                    stack[-1] += stacktop * 2
                case _:
                    stack[-1] += 1
        return stack[-1]

    def __iter__(self):
        return self

    def __next__(self) -> tuple[tuple[int, int], Color]:
        buffer: tuple[tuple[int, int], Color] | None = None
        while self.codePtr < self.codeSize and buffer is None:
            match self.code[self.codePtr]:
                case 'C':
                    self.colorPtr = (self.colorPtr + 1) & 7
                    self.stepCount += 1
                case 'F':
                    self.x = (self.x + dirPalette[self.dirPtr][0]) & 255
                    self.y = (self.y + dirPalette[self.dirPtr][1]) & 255
                    # pg y-axis is top to bottom
                    buffer = ((self.x, 256 - self.y),
                              colorPalette[self.colorPtr])
                    self.stepCount += 1
                case 'R':
                    self.dirPtr = (self.dirPtr + 1) & 7
                    self.stepCount += 1
                case '[':
                    self.blockStack.append(self.codePtr)
                case ']':
                    stacktop = self.blockStack.pop()
                    if stacktop != self.codePtr:
                        self.blockStack.append(self.codePtr)
                        self.codePtr = stacktop
            if self.isReportProgress:
                print(f"{self.stepCount} / {self.codeTotalLen}",
                      end="\x1b[0K\r")
            self.codePtr += 1
        if buffer is not None:
            return buffer
        else:
            self.isRunning = False
            print("")
            raise StopIteration


class App:
    def __init__(self, code: str, reportProress: bool = True) -> None:
        """
        reportProress is passed to CFR
        """
        print("initiating")
        # game internal
        self.isRunning: bool = True
        self.isReportProgress: bool = reportProress
        self.interpreter: CFR = CFR(code, reportProress)
        print(f"Total steps: {self.interpreter.codeTotalLen}")
        # pg internal
        pg.init()
        self.fps: int | float = 30
        self.clock: pg.time.Clock = pg.time.Clock()
        self.screen: pg.Surface = pg.display.set_mode((256, 256))

    def processEvent(self) -> None:
        for e in pg.event.get():
            if e.type == pg.QUIT:
                self.isRunning = False
            elif e.type == pg.KEYDOWN:
                if e.key == pg.K_q:
                    self.isRunning = False

    def run(self, fastDraw: bool = False) -> None:
        """
        setting fastDraw False waits for each tick
        """
        print("Running")
        isHaltedReported: bool = False
        while self.isRunning:
            self.processEvent()
            if not self.interpreter.isValid:
                self.screen.fill(Color.RED.value)
                pg.display.update()
                self.interpreter.isRunning = False
            if self.interpreter.isRunning \
                    and (inst := next(self.interpreter, None)) is not None:
                self.screen.set_at(inst[0], inst[1].value)
                pg.display.update()
            elif not isHaltedReported:
                print("halted")
                isHaltedReported = True
                fastDraw = False
            if not fastDraw:
                self.clock.tick(self.fps)
        pg.quit()

