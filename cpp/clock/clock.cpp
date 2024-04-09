#include <chrono>
#include <ctime>
#include <Fl/Fl.H>
#include <FL/Enumerations.H>
#include <FL/Fl_Window.H>
#include <Fl/Fl_Widget.H>
#include <Fl/Fl_draw.H>

constexpr double minSleepTime_s = 0.0625;

// do not want to include <algorithm> for these two
inline double max(const double &a, const double &b) { return a > b ? a : b; }
inline double min(const double &a, const double &b) { return a < b ? a : b; }

class Clock : public Fl_Widget {
private:
    static constexpr uint8_t onSegments[10] = {119, 36, 93, 109, 46, 107, 123, 37, 127, 111};

    int minSegWidth;
    Fl_Color fillColorOn, fillColorOff;
    uint8_t segStates[6] = {8, 8, 8, 8, 8, 8};

    // inst static buffer for drawSegment
    double _xCoorBuff[6] = {0.0}, _yCoorBuff[6] = {0.0};

    void drawSegment(
            double centerX, double centerY,
            double halfLen, double halfWidth,
            bool isHorizontal,
            bool isSegOn) {
        double halfTopLen = halfLen - halfWidth;
        // unrolled
        _xCoorBuff[0] = halfTopLen;
        _yCoorBuff[0] = -halfWidth;
        _xCoorBuff[1] = halfLen;
        _yCoorBuff[1] = 0;
        _xCoorBuff[2] = halfTopLen;
        _yCoorBuff[2] = halfWidth;
        _xCoorBuff[3] = -halfTopLen;
        _yCoorBuff[3] = halfWidth;
        _xCoorBuff[4] = -halfLen;
        _yCoorBuff[4] = 0;
        _xCoorBuff[5] = -halfTopLen;
        _yCoorBuff[5] = -halfWidth;
        if (!isHorizontal) {
            for (uint8_t i = 0; i < 6; ++i) {
                halfLen = _xCoorBuff[i];
                _xCoorBuff[i] = _yCoorBuff[i];
                _yCoorBuff[i] = -halfLen;
            }
        }
        fl_color(isSegOn ? fillColorOn : fillColorOff);
        fl_begin_polygon();
        for (uint8_t i = 0; i < 6; ++i) {
            fl_vertex(centerX + _xCoorBuff[i], centerY + _yCoorBuff[i]);
        }
        fl_end_polygon();
    }

    inline static constexpr uint8_t segmentBitMask(uint8_t segIdx) {
        return 1 << segIdx;
    }

    inline void drawDigit(
            double topLeftX, double topLeftY, 
            double digW, double digH,
            double segW,
            uint8_t state) {
        double halfSegWidth = segW / 2, 
            halfHoriSegLen = (digW - segW) / 2.0, 
            halfVertSegLen = (digH - segW) / 4.0;
        // unrolled
        drawSegment(
                topLeftX + halfSegWidth + halfHoriSegLen,
                topLeftY + halfSegWidth,
                halfHoriSegLen, halfSegWidth,
                true, state & segmentBitMask(0));
        drawSegment(
                topLeftX + halfSegWidth,
                topLeftY + halfSegWidth + halfVertSegLen,
                halfVertSegLen, halfSegWidth,
                false, state & segmentBitMask(1));
        drawSegment(
                topLeftX + halfSegWidth + halfHoriSegLen * 2,
                topLeftY + halfSegWidth + halfVertSegLen,
                halfVertSegLen, halfSegWidth,
                false, state & segmentBitMask(2));
        drawSegment(
                topLeftX + halfSegWidth + halfHoriSegLen,
                topLeftY + halfSegWidth + halfVertSegLen * 2,
                halfHoriSegLen, halfSegWidth,
                true, state & segmentBitMask(3));
        drawSegment(
                topLeftX + halfSegWidth,
                topLeftY + halfSegWidth + halfVertSegLen * 3,
                halfVertSegLen, halfSegWidth,
                false, state & segmentBitMask(4));
        drawSegment(
                topLeftX + halfSegWidth + halfHoriSegLen * 2,
                topLeftY + halfSegWidth + halfVertSegLen * 3,
                halfVertSegLen, halfSegWidth,
                false, state & segmentBitMask(5));
        drawSegment(
                topLeftX + halfSegWidth + halfHoriSegLen,
                topLeftY + halfSegWidth + halfVertSegLen * 4,
                halfHoriSegLen, halfSegWidth,
                true, state & segmentBitMask(6));
    }

    inline void drawColon(
            double topLeftX, double topLeftY, 
            double w, double h,
            double dotSize) {
        double deltaW = (w - dotSize) / 2.0, deltaH = (h - dotSize * 2) / 3.0;
        fl_color(fillColorOn);
        fl_begin_polygon();
        fl_vertex(topLeftX + deltaW, topLeftY + deltaH);
        fl_vertex(topLeftX + deltaW + dotSize, topLeftY + deltaH);
        fl_vertex(topLeftX + deltaW + dotSize, topLeftY + deltaH + dotSize);
        fl_vertex(topLeftX + deltaW, topLeftY + deltaH + dotSize);
        fl_end_polygon();
        topLeftY += deltaH + dotSize;
        fl_begin_polygon();
        fl_vertex(topLeftX + deltaW, topLeftY + deltaH);
        fl_vertex(topLeftX + deltaW + dotSize, topLeftY + deltaH);
        fl_vertex(topLeftX + deltaW + dotSize, topLeftY + deltaH + dotSize);
        fl_vertex(topLeftX + deltaW, topLeftY + deltaH + dotSize);
        fl_end_polygon();
    }

    static void static_updateClock_cb(void *widgetPtr) {
        reinterpret_cast<Clock *>(widgetPtr)->updateClock_cb();
    }

    void updateClock_cb(void) {
        double currTimeSubSec_s = updateTimeStates();
        Fl::repeat_timeout(
                1.0 + minSleepTime_s - currTimeSubSec_s,
                static_updateClock_cb, this);
    }

public:
    Clock(
            int X, int Y, int W, int H,
            int minSegmentWidth = 8,
            Fl_Color colorOn = FL_BLACK,
            Fl_Color colorOff = FL_BACKGROUND_COLOR,
            const char *L = nullptr): 
        Fl_Widget(X, Y, W, H, L), 
        minSegWidth(minSegmentWidth), 
        fillColorOn(colorOn), fillColorOff(colorOff) { 
            Fl::add_timeout(0.3, static_updateClock_cb, this);  // startup time
        }

    inline double updateTimeStates(void) {
        // update internal timer stat and force redraw to happen
        // return millisecond part of current time
        // cpp17
        auto tp = std::chrono::system_clock::now();
        time_t t = std::chrono::system_clock::to_time_t(tp);
        tm local_tm = *std::localtime(&t);
        // TODO: can we optimize these?
        segStates[0] = onSegments[local_tm.tm_hour / 10];
        segStates[1] = onSegments[local_tm.tm_hour % 10];
        segStates[2] = onSegments[local_tm.tm_min / 10];
        segStates[3] = onSegments[local_tm.tm_min % 10];
        segStates[4] = onSegments[local_tm.tm_sec / 10];
        segStates[5] = onSegments[local_tm.tm_sec % 10];
        redraw();
        // TODO: better way?
        return (std::chrono::time_point_cast<std::chrono::milliseconds>(tp)
                .time_since_epoch().count() % 1000) / 1000.0;
    }

    void draw(void) {
        // cannot precompute: must change with resize
        constexpr double 
            digitWidthRatio = 1.0 / 9,
            digitSepWidthRatio = 1.0 / 40,
            gpSepWidthRatio = 1.0 / 12,
            digitHeightRatio = 2.0 / 3,
            minSegRatio = 1.0 / 5;  // over digW and digH
        constexpr double 
            marginHRatio = (1.0 - digitHeightRatio) / 2.0,
            marginWRatio = (1.0 - digitWidthRatio * 6 
                    - digitSepWidthRatio * 3 - gpSepWidthRatio * 2) / 2.0;

        double W = w(), H = h();
        double digW = W * digitWidthRatio, 
               digSepW = W * digitSepWidthRatio,
               gpSepW = W * gpSepWidthRatio,
               digH = H * digitHeightRatio;
        double segW = max(minSegWidth, min(digH, digW) * minSegRatio),
               marginH = marginHRatio * H,
               marginW = marginWRatio * W;
        double X = x() + marginW, Y = y() + marginH;
        for (uint8_t gpIdx = 0; gpIdx < 3; ++gpIdx) {
            drawDigit(X, Y, digW, digH, segW, segStates[gpIdx * 2]);
            drawDigit(X + digW + digSepW, Y, digW, digH, segW, segStates[gpIdx * 2 + 1]);
            if (gpIdx != 2) {
                drawColon(X + digW * 2 + digSepW, Y, gpSepW, digH, segW);
            }
            X += digW * 2 + digSepW + gpSepW;
        }
    }
};

int main(int, char **) {
    int w = 800, h = 330;
    Fl_Window win(0, 0, w, h, "Clock");
    win.begin();
        Clock c(0, 0, w, h);
    win.end();
    win.resizable(&c);
    win.show();
    return Fl::run();
}

