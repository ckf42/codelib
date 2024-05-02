#ifndef MidButton_h
#define MidButton_h

#ifdef DEBUG
#include <iostream>
#endif

#include <FL/Enumerations.H>
#include <FL/Fl_Button.H>

class MidButton : public Fl_Button {
public:
    enum struct BtnMode : uint8_t {
        NORMAL = 0,
        SURPRISED = 1,
        WON = 2,
        DEAD = 3,
    };

private:
    static constexpr char labelArr[][5] = {
        "\U0001F642",  // normal
        "\U0001F62E",  // surprised
        "\U0001F60E",  // won
        "\U0001F635",  // dead
    };  // all 4 bytes (+ '\0') long

    BtnMode m_mode;

    inline void _setLabel(BtnMode idx) {
        this->label(labelArr[static_cast<uint8_t>(idx)]);
        this->redraw_label();
    }

public:
    static constexpr int
        dimension = 30,
        fontsize = 18;

    MidButton(int x, int y):
        Fl_Button(x, y, dimension, dimension, labelArr[0]),
        m_mode(BtnMode::NORMAL) {
        this->labelsize(fontsize);
        this->align(FL_ALIGN_CENTER | FL_ALIGN_INSIDE);
    }

    inline void setMode(BtnMode mode) {
        if (mode != m_mode) {
#ifdef DEBUG
            std::printf("set btn mode=%d\n", static_cast<uint8_t>(mode));
#endif
            m_mode = mode;
            _setLabel(mode);
        }
    }
    
    void draw(void) {
        if (value() == 1) {
            _setLabel(BtnMode::NORMAL);
        } else {
            _setLabel(m_mode);
        }
        Fl_Button::draw();
    }

};

#endif

