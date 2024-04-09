#include <chrono>
#include <climits>
#include <cstdint>
#include <stack>
#include <string>
#include <string>
#include <thread>
#include <Fl/Fl.H>
#include <FL/Enumerations.H>
#include <Fl/Fl_Widget.H>
#include <Fl/Fl_Window.H>
#include <Fl/Fl_draw.H>

constexpr unsigned counterDrawHeight = 20;

class CFRS : public Fl_Widget {
private:
    static constexpr Fl_Color colorPalette[8] = {
        FL_WHITE, FL_BLACK, FL_BLUE, FL_GREEN, 
        FL_CYAN, FL_RED, FL_MAGENTA, FL_YELLOW
    };
    static constexpr int8_t dx[8] = {0, 1, 1, 1, 0, -1, -1, -1};
    static constexpr int8_t dy[8] = {-1, -1, 0, 1, 1, 1, 0, -1};

    bool isCodeValid, isOutputPainted, isCodeTooLong;
    std::string codeStr, codeLenSuffix;
    unsigned codeTotalLen;  // max possible is 2**128, will not show this if too long
    // can save space by combining, but probably not necessary
    uint8_t turtleX, turtleY, turtleDir, turtleColor;

    inline void _toNextDir(void) {
        ++turtleDir;
        turtleDir &= 7;
    }
    inline void _toNextColor(void) {
        ++turtleColor;
        turtleColor &= 7;
    }
    inline void _moveForward(void) {
        turtleX += dx[turtleDir];
        turtleY += dy[turtleDir];
    }

public:
    CFRS(int x, int y, int w, int h, const char *code, char *l = nullptr):
            Fl_Widget(x, y, w, h, l),
            isCodeValid(true), isOutputPainted(false), isCodeTooLong(false),
            codeStr(), codeLenSuffix(), codeTotalLen(0),
            turtleX(127), turtleY(127), turtleDir(0), turtleColor(0) {
        while (*code != 0) {
            char c = *code & 0xDF;
            switch (c) {
                case 'C':
                case 'F':
                case 'R':
                case 'S':
                case '[':
                case ']':
                    codeStr += c;
                    break;
            }
            ++code;
        }
        if (codeStr.size() > 256) {
            isCodeValid = false;
        } else {
            unsigned depth = 0;
            for (char &c : codeStr) {
                if (c == '[') {
                    ++depth;
                } else if (c == ']') {
                    if (depth == 0) {
                        isCodeValid = false;
                        break;
                    }
                    --depth;
                }
            }
        }
        if (isCodeValid) {
            // TODO: combine with validation?
            std::stack<unsigned> repeatSizes;
            repeatSizes.push(0);
            unsigned stackTop;
            for (char &c : codeStr) {
                switch (c) {
                    case '[':
                        repeatSizes.push(0);
                        break;
                    case ']':
                        stackTop = repeatSizes.top();
                        repeatSizes.pop();
                        if (stackTop > UINT_MAX / 2 
                                || repeatSizes.top() > UINT_MAX - stackTop * 2) {
                            isCodeTooLong = true;
                        } else {
                            repeatSizes.top() += stackTop * 2;
                        }
                        break;
                    default:
                        if (repeatSizes.top() < UINT_MAX) {
                            ++repeatSizes.top();
                        } else {
                            isCodeTooLong = true;
                        }
                        break;
                }
            }
            while (!repeatSizes.empty() && !isCodeTooLong) {
                if (codeTotalLen > UINT_MAX - repeatSizes.top()) {
                    isCodeTooLong = true;
                } else {
                    codeTotalLen += repeatSizes.top();
                }
                repeatSizes.pop();
            }
            if (isCodeTooLong) {
                codeLenSuffix = "";
            } else {
                codeLenSuffix = " / " + std::to_string(codeTotalLen);
            }
        }
        fl_font(FL_HELVETICA, 14);
    }

    void draw(void) {
        if (isOutputPainted) {
            return;
        }
        if (!isCodeValid) {
            fl_color(FL_RED);
            fl_rectf(0, 0, 256, 256);
            fl_color(FL_WHITE);
            fl_rectf(0, 256, 256, counterDrawHeight);
            fl_color(FL_BLACK);
            fl_draw("Invalid", 5, 256 + counterDrawHeight - 5);
            isOutputPainted = true;
            return;
        } 
        fl_color(FL_BLACK);
        fl_rectf(0, 0, 256, 256);
        fl_color(FL_WHITE);
        fl_rectf(0, 256, 256, counterDrawHeight);
        fl_color(FL_BLACK);
        fl_draw(("0" + codeLenSuffix).c_str(), 5, 256 + counterDrawHeight - 5);
        unsigned codeIdx = 0, stepCounter = 0;
        std::stack<unsigned> loopPosStack;
        while (codeIdx < codeStr.size()) {
            switch (codeStr[codeIdx]) {
                case 'C':
                    ++stepCounter;
                    _toNextColor();
                    break;
                case 'F':
                    ++stepCounter;
                    _moveForward();
                    fl_color(colorPalette[turtleColor]);
                    fl_point(turtleX, turtleY);
                    break;
                case 'R':
                    ++stepCounter;
                    _toNextDir();
                    break;
                case 'S':
                    ++stepCounter;
                    // this pauses the whole process
                    // TODO: how to fix?
                    // NOTE: Fl::wait will make image drawn twice. multithread?
                    std::this_thread::sleep_for(std::chrono::milliseconds(20));
                    break;
                case '[':
                    loopPosStack.push(codeIdx);
                    break;
                case ']':
                    if (loopPosStack.top() != codeIdx) {
                        std::swap(loopPosStack.top(), codeIdx);
                    } else {
                        loopPosStack.pop();
                    }
                    break;
            }
            // TODO: how to reduce flickering?
            fl_color(FL_WHITE);
            fl_rectf(0, 256, 256, counterDrawHeight);
            fl_color(FL_BLACK);
            fl_draw((std::to_string(stepCounter) + codeLenSuffix).c_str(),
                    5, 256 + counterDrawHeight - 5);
            ++codeIdx;
        }
        isOutputPainted = true;
    }
};


int main(int argv, char **argc) {
    if (argv != 2) {
        Fl::fatal("Usage: %s CODE", argc[0]);
        return 1;
    }
    Fl_Window win(0, 0, 256, 256 + counterDrawHeight, "Testing");
    win.begin();
        CFRS c(0, 0, 256, 256 + counterDrawHeight, argc[1]);
    win.end();
    win.show();
    return Fl::run();
}

