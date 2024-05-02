#ifndef ValueDisplay_h
#define ValueDisplay_h


#ifdef DEBUG
#include <iostream>
#endif

#include <string>
#include <FL/Fl.H>
#include <FL/Fl_Widget.H>
#include <FL/Fl_Box.H>

// simple wrapper around Fl_Box
class ValueDisplay : public Fl_Box {
private:
    int m_val;
    bool m_timerActive;

    inline void _showValue(void) {
        std::string resStr = std::to_string(m_val > 0 ? m_val : ((-m_val) % 100));
        if (m_val < 0) {
            resStr = "-" + std::string(2 - resStr.size(), '0') + resStr;
        } else {
            resStr = std::string(3 - resStr.size(), '0') + resStr;
        }
#ifdef DEBUG
        std::printf("display string: %s\n", resStr.c_str());
#endif
        this->copy_label(resStr.c_str());
        this->redraw_label();
    }

public:
    static constexpr int
        width = 43, height = 30,
        minVal = -30 * 24,  // = -maxWCount * maxHCount
        maxVal = 999,
        fontsize = 21;

    ValueDisplay(int x, int y):
        Fl_Box(x, y, width, height, "000"),
        m_val(0), m_timerActive(false) {
        this->box(FL_BORDER_BOX);
        this->color(FL_BLACK);
        this->labelcolor(FL_RED);
        this->labeltype(FL_NORMAL_LABEL);
        this->labelsize(fontsize);
        this->labelfont(FL_SCREEN_BOLD);
        this->align(FL_ALIGN_CENTER | FL_ALIGN_INSIDE);
    }

    // do not capture event
    inline int handle(int) {
        return 0;
    }

    inline void setVal(int newVal) {
        newVal = (newVal >= maxVal) ? maxVal : (newVal <= minVal ? minVal : newVal);
        if (newVal != m_val) {
            m_val = newVal;
#ifdef DEBUG
            std::printf("set val=%d\n", newVal);
#endif
            _showValue();
        }
    }

    inline void increVal(void) {
        m_val = (m_val == maxVal) ? maxVal : (m_val + 1);
        _showValue();
    }

    static void increTimer_cb(void *wig) {
        ValueDisplay *ptr = reinterpret_cast<ValueDisplay *>(wig);
        if (ptr->m_timerActive) {
            ptr->increVal();
            Fl::repeat_timeout(1.0, ValueDisplay::increTimer_cb, wig);
        }
    }

    inline bool isTimerActive(void) const {
        return m_timerActive;
    }

    inline void startTimer(void) {
        m_timerActive = true;
        Fl::add_timeout(1.0, increTimer_cb, this);
    }

    inline void stopTimer(void) {
        m_timerActive = false;
    }

    inline void resetTimer(void) {
        stopTimer();
        setVal(0);
    }

};

#endif
