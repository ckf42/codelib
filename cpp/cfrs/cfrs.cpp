#include <atomic>
#include <mutex>
#include <queue>
#include <stack>
#include <string>
#include <thread>
#include <Fl/Fl.H>
#include <FL/Enumerations.H>
#include <FL/Fl_draw.H>
#include <Fl/Fl_Window.H>
#include <Fl/Fl_Widget.H>

constexpr unsigned counterDrawHeight = 20;

class CFRS_Widget : public Fl_Widget {
private:
    static constexpr Fl_Color colorPalette[8] = {
        FL_WHITE, FL_BLACK, FL_BLUE, FL_GREEN, 
        FL_CYAN, FL_RED, FL_MAGENTA, FL_YELLOW
    };
    static constexpr int8_t dx[8] = {0, 1, 1, 1, 0, -1, -1, -1};
    static constexpr int8_t dy[8] = {-1, -1, 0, 1, 1, 1, 0, -1};

    std::string codeStr;
    bool isBackgroundDrawn;
    struct PixelData {
        uint8_t x, y, c;
        PixelData(uint8_t x, uint8_t y, uint8_t c): x(x), y(y), c(c) {}
    };
    std::queue<PixelData> pixelQueue;
    std::mutex pixelQueue_mtx;
    std::atomic_bool isCodeEnded;
    std::atomic<unsigned> stepCounter;
    std::thread interpreterThread;

    void codeInterpreter_worker(void) {
        uint8_t turtleX = 127, turtleY = 127, turtleDir = 0, turtleColor = 0;
        unsigned codeIdx = 0;
        std::unique_lock pixelQueue_lk(pixelQueue_mtx, std::defer_lock);
        std::stack<unsigned> loopPosStack;
        while (codeIdx < codeStr.size() && !isCodeEnded) {
            switch (codeStr[codeIdx]) {
                case 'C':
                    ++stepCounter;
                    ++turtleColor;
                    turtleColor &= 7;
                    break;
                case 'F':
                    ++stepCounter;
                    turtleX += dx[turtleDir];
                    turtleY += dy[turtleDir];
                    pixelQueue_lk.lock();
                    pixelQueue.emplace(turtleX, turtleY, turtleColor);
                    redraw();
                    if (pixelQueue.size() > 10) {
                        Fl::awake();
                    }
                    pixelQueue_lk.unlock();
                    break;
                case 'R':
                    ++stepCounter;
                    ++turtleDir;
                    turtleDir &= 7;
                    break;
                case 'S':
                    ++stepCounter;
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
            ++codeIdx;
        }
        isCodeEnded = true;
        redraw();
    }

    static void startInterpreterThread(void *obj) {
        CFRS_Widget *ptr = reinterpret_cast<CFRS_Widget*>(obj);
        ptr->interpreterThread = std::thread(
                &CFRS_Widget::codeInterpreter_worker,
                ptr);
    }

public:
    CFRS_Widget(
            int x, int y, int w, int h,
            const char *codePtr,
            const char *l = nullptr):
        Fl_Widget(x, y, w, h, l),
        codeStr(),
        isBackgroundDrawn(false),
        pixelQueue(), pixelQueue_mtx(),
        isCodeEnded(false), stepCounter(0),
        interpreterThread() {
        // load code and normalize
        while (*codePtr != 0) {
            char c = *codePtr & 0xDF;  // cheap toUpper
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
            ++codePtr;
        }
        // verify
        bool isCodeValid = true;
        if (codeStr.size() > 256) {
            isCodeValid = false;
        } else {
            unsigned depth = 0;
            for (const char &c : codeStr) {
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
        pixelQueue.emplace(0, 0, isCodeValid ? 1 : 5);
        fl_font(FL_HELVETICA, 14);
        if (isCodeValid) {
            Fl::add_timeout(
                    0.1,
                    CFRS_Widget::startInterpreterThread,
                    this
            );
        }
    }

    ~CFRS_Widget() {
        if (interpreterThread.joinable()) {
            isCodeEnded = true;
            interpreterThread.join();
        }
    }

    void draw(void) {
        PixelData px(0, 0, 0);
        if (!isBackgroundDrawn) {
            {
                std::lock_guard pixelQueue_lk(pixelQueue_mtx);
                px = pixelQueue.front();
                pixelQueue.pop();
            }
            fl_color(colorPalette[px.c]);
            fl_rectf(0, 0, 256, 256);
            isBackgroundDrawn = true;
        }
        {
            std::lock_guard pixelQueue_lk(pixelQueue_mtx);
            while (!pixelQueue.empty()) {
                px = pixelQueue.front();
                pixelQueue.pop();
                fl_color(colorPalette[px.c]);
                fl_point(px.x, px.y);
            }
        }
        fl_color(FL_WHITE);
        fl_rectf(0, 256, 256, counterDrawHeight);
        fl_color(FL_BLACK);
        fl_draw(std::to_string(stepCounter).c_str(), 5, 256 + counterDrawHeight - 5);
    }
};

int main(int argc, char **argv) {
    if (argc != 2) {
        Fl::fatal("Usage: %s CODE", argv[0]);
        return 1;
    }
    Fl::lock();
    Fl_Window win(0, 0, 256, 256 + counterDrawHeight, "CFRS");
    win.begin();
        CFRS_Widget c(0, 0, 256, 256 + counterDrawHeight, argv[1]);
    win.end();
    win.show();
    return Fl::run();
}
