#ifndef CustomFieldModal_h
#define CustomFieldModal_h

#include <FL/Fl_Button.H>
#include <FL/Fl_Value_Input.H>
#include <FL/Fl_Widget.H>
#include <FL/Fl_Window.H>

class CustomFieldModal : public Fl_Window {
private:
    static constexpr int
        winW = 224, winH = 133,
        inputXOffset = 65, inputYOffset = 31, inputYGap = 5,
        inputW = 44, inputH = 22,
        btnXOffset = 27,
        btnW = 69, btnH = 27;

    bool m_submitted = false;

    Fl_Value_Input *m_hInput = nullptr, *m_wInput = nullptr, *m_mInput = nullptr;
    Fl_Button *m_btnConfirm = nullptr, *m_btnCancel = nullptr;

public:
    CustomFieldModal(int defaultW, int defaultH, int defaultM):
        Fl_Window(winW, winH, "Custom Field") {
        this->begin();
            m_hInput = new Fl_Value_Input(
                    inputXOffset, inputYOffset,
                    inputW, inputH, "Height: ");
            m_hInput->maximum(9999);
            m_hInput->maximum(-9999);
            m_hInput->value(defaultH);
            m_wInput = new Fl_Value_Input(
                    inputXOffset, inputYOffset + inputH + inputYGap,
                    inputW, inputH, "Width: ");
            m_wInput->maximum(9999);
            m_wInput->maximum(-9999);
            m_wInput->value(defaultW);
            m_mInput = new Fl_Value_Input(
                    inputXOffset, inputYOffset + (inputH + inputYGap) * 2,
                    inputW, inputH, "Mines: ");
            m_mInput->maximum(9999);
            m_mInput->maximum(-9999);
            m_mInput->value(defaultM);
            m_btnConfirm = new Fl_Button(
                    winW - btnXOffset - btnW, inputYOffset,
                    btnW, btnH, "OK");
            m_btnCancel = new Fl_Button(
                    winW - btnXOffset - btnW, inputYOffset + (inputH + inputYGap) * 2 + inputH - btnH,
                    btnW, btnH, "Cancel");
        this->end();
        this->set_modal();
        m_btnConfirm->callback(userComfirmed_cb, this);
        m_btnCancel->callback(userCancelled_cb, this);
    }

    CustomFieldModal& operator=(const CustomFieldModal&) = delete;
    CustomFieldModal(const CustomFieldModal&) = delete;

    static void userComfirmed_cb(Fl_Widget *, void* data) {
        CustomFieldModal *ptr = reinterpret_cast<CustomFieldModal *>(data);
        ptr->m_submitted = true;
        ptr->hide();
    }

    static void userCancelled_cb(Fl_Widget *, void* data) {
        CustomFieldModal *ptr = reinterpret_cast<CustomFieldModal *>(data);
        ptr->m_submitted = false;
        ptr->hide();
    }

    inline bool isSubmitted(void) const {
        return m_submitted;
    }

    inline int getW(void) const {
        return static_cast<int>(m_wInput->value());
    }

    inline int getH(void) const {
        return static_cast<int>(m_hInput->value());
    }

    inline int getMine(void) const {
        return static_cast<int>(m_mInput->value());
    }

};

#endif
