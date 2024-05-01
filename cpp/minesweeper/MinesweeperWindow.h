#ifndef MinesweeperWindow_h
#define MinesweeperWindow_h

#ifdef DEBUG
#include <iostream>
#include <Fl/names.h>
#endif

#include <FL/Enumerations.H>
#include <FL/Fl.H>
#include <FL/Fl_Group.H>
#include <FL/Fl_Menu_Bar.H>
#include <FL/Fl_Menu_Item.H>
#include <FL/Fl_Widget.H>
#include <FL/Fl_Window.H>

#include "MineField.h"
#include "ValueDisplay.h"
#include "MidButton.h"
#include "CustomFieldModal.h"

class MinesweeperWindow : public Fl_Window {
private:
    static constexpr uchar menuFontSize = 12;
    static constexpr int 
        marginDim = 9,
        menuBarHeight = 22,
        headerHeight = 45,
        valueDisplayXOffset = 6, headerContentYOffset = 8;

    Fl_Menu_Bar *m_menuBar = nullptr;
    Fl_Group *m_header = nullptr;
    ValueDisplay *m_remainMineCount = nullptr, *m_timer = nullptr;
    MidButton *m_btn = nullptr;
    MineField *m_mf = nullptr;

    inline void _resizeWindow(void) {
        int mfY = marginDim * 2 + menuBarHeight + headerHeight;
        this->size(
                m_mf->w() + marginDim * 2,
                mfY + m_mf->h() + marginDim);
        m_menuBar->resize(0, 0, this->w(), menuBarHeight);
        m_header->resize(
                marginDim, menuBarHeight + marginDim,
                this->w() - marginDim * 2, headerHeight);
        m_remainMineCount->position(
                m_header->x() + valueDisplayXOffset,
                m_header->y() + headerContentYOffset);
        m_timer->position(
                m_header->x() + m_header->w() - valueDisplayXOffset - ValueDisplay::width,
                m_header->y() + headerContentYOffset);
        m_btn->position(
                m_header->x() + (m_header->w() - MidButton::dimension) / 2,
                m_header->y() + headerContentYOffset);
        m_mf->position(marginDim, mfY);
    }

    void _resetBoard(int wCount, int hCount, int mineCount) {
        Fl::delete_widget(m_mf);
        this->begin();
        m_mf = new MineField(
                marginDim, marginDim * 2 + menuBarHeight + headerHeight,
                wCount, hCount, mineCount);
        this->end();
        _resizeWindow();
        m_remainMineCount->setVal(m_mf->getMineCount());
        m_btn->setMode(MidButton::BtnMode::NORMAL);
        m_timer->resetTimer();
    }

    // update widgets display
    inline void _updateDisplay(void) {
#ifdef DEBUG
        std::printf("update called\n");
#endif
        if (Fl::event_inside(m_mf) != 0) {
            m_remainMineCount->setVal(m_mf->getMineCount() - m_mf->getFlagCount());
#ifdef DEBUG
            std::printf("updating remain count\n");
#endif
        }
        MineField::GameState gs = m_mf->getGameState();
        if (gs != MineField::GameState::ACTIVE) {
            m_timer->stopTimer();
            m_btn->setMode(
                    gs == MineField::GameState::DEAD
                    ? MidButton::BtnMode::DEAD
                    : MidButton::BtnMode::WON);
#ifdef DEBUG
            std::printf("updating btn mode\n");
#endif
        } else if (m_mf->isGameStarted() && !m_timer->isTimerActive()) {
            m_timer->startTimer();
#ifdef DEBUG
            std::printf("starting timer\n");
#endif
        }
    }

public:
    static void startNew_cb(Fl_Widget *, void *win) {
        MinesweeperWindow *ptr = reinterpret_cast<MinesweeperWindow *>(win);
        ptr->_resetBoard(
                ptr->m_mf->getWCount(),
                ptr->m_mf->getHCount(),
                ptr->m_mf->getMineCount());
    }

    static void startBeginner_cb(Fl_Widget *menuItem, void *win) {
        reinterpret_cast<Fl_Menu_Item *>(menuItem)->setonly();
        reinterpret_cast<MinesweeperWindow *>(win)->_resetBoard(9, 9, 10);
    }

    static void startIntermediate_cb(Fl_Widget *menuItem, void *win) {
        reinterpret_cast<Fl_Menu_Item *>(menuItem)->setonly();
        reinterpret_cast<MinesweeperWindow *>(win)->_resetBoard(16, 16, 40);
    }

    static void startExpert_cb(Fl_Widget *menuItem, void *win) {
        reinterpret_cast<Fl_Menu_Item *>(menuItem)->setonly();
        reinterpret_cast<MinesweeperWindow *>(win)->_resetBoard(30, 16, 99);
    }

    static void startCustom_cb(Fl_Widget *, void *win) {
        MinesweeperWindow *ptr = reinterpret_cast<MinesweeperWindow *>(win);
        CustomFieldModal dlg(
                ptr->m_mf->getWCount(), ptr->m_mf->getHCount(),
                ptr->m_mf->getMineCount());
        dlg.show();
        while (dlg.shown()) {
            Fl::wait();
        }
        if (dlg.isSubmitted()) {
            ptr->_resetBoard(dlg.getW(), dlg.getH(), dlg.getMine());
        }
    }

    static void exit_cb(Fl_Widget *, void *win) {
        reinterpret_cast<MinesweeperWindow *>(win)->hide();
    }

    MinesweeperWindow& operator=(const MinesweeperWindow&) = delete;
    MinesweeperWindow(const MinesweeperWindow&) = delete;

    MinesweeperWindow(void):
        Fl_Window(0, 0, "Minesweeper") {
        Fl_Menu_Item menuItems[] = {
            {"&Game", FL_ALT + 'g', nullptr, nullptr, FL_SUBMENU,
                static_cast<uchar>(FL_NORMAL_LABEL), 0, menuFontSize, 0},
                {"&New", FL_F + 2, startNew_cb, this, FL_MENU_DIVIDER,
                    static_cast<uchar>(FL_NORMAL_LABEL), 0, menuFontSize, 0},
                {"&Beginner", 0, startBeginner_cb, this, FL_MENU_RADIO | FL_MENU_VALUE,
                    static_cast<uchar>(FL_NORMAL_LABEL), 0, menuFontSize, 0},
                {"&Intermediate", 0, startIntermediate_cb, this, FL_MENU_RADIO,
                    static_cast<uchar>(FL_NORMAL_LABEL), 0, menuFontSize, 0},
                {"&Expert", 0, startExpert_cb, this, FL_MENU_RADIO,
                    static_cast<uchar>(FL_NORMAL_LABEL), 0, menuFontSize, 0},
                {"&Custom...", 0, startCustom_cb, this, FL_MENU_DIVIDER | FL_MENU_RADIO,
                    static_cast<uchar>(FL_NORMAL_LABEL), 0, menuFontSize, 0},
                {"E&xit", 0, exit_cb, this, 0,
                    static_cast<uchar>(FL_NORMAL_LABEL), 0, menuFontSize, 0},
                {0, 0, 0, 0, 0, 0, 0, 0, 0},
            {0, 0, 0, 0, 0, 0, 0, 0, 0}
        };
        this->begin();
            m_menuBar = new Fl_Menu_Bar(0, 0, 0, 0);
            m_menuBar->copy(menuItems);
            m_header = new Fl_Group(0, 0, 0, 0);
            m_header->begin();
                m_remainMineCount = new ValueDisplay(0, 0);
                m_timer = new ValueDisplay(0, 0);
                m_btn = new MidButton(0, 0);
            m_header->end();
            m_header->box(FL_DOWN_BOX);
            m_mf = new MineField(marginDim, marginDim * 2 + menuBarHeight + headerHeight);
            m_remainMineCount->setVal(m_mf->getMineCount());
        this->end();
        this->_resizeWindow();
        this->resizable(nullptr);
        this->box(FL_BORDER_BOX);
        m_btn->callback(startNew_cb, this);
    }

    int handle(int event) {
#ifdef DEBUG
        if (event <= 30) {
            std::printf("win event %s\n", fl_eventnames[event]);
        } else {
            std::printf("win event custom %d\n", event);
        }
#endif
#ifndef DEBUG
        // override fltk default Esc-to-escape
        if (event == FL_KEYDOWN && Fl::event_key(FL_Escape) != 0) {
            return 1;
        }
#endif
        // EVENT_STATE_UPDATED should only be sent by subwidget
        // need to do this because this->handle() does not receive event that mf consumed
        // (which mf needs to in order to capture events like FL_DRAG)
        // for mf to tell *this to update its display, sending a custom event seems the most reasonable
        // looks like anti-pattern
        // TODO: better approach?
        if (m_mf->getGameState() == MineField::GameState::ACTIVE) {
#ifdef DEBUG
            std::printf(
                    "pushed? %d, released? %d, leftbtn? %d\n",
                    event == FL_PUSH, event == FL_RELEASE, Fl::event_button1() != 0
                    );
#endif
            if (event == FL_PUSH && Fl::event_button1() != 0) {
                m_btn->setMode(MidButton::BtnMode::SURPEISED);
            } else if (event == FL_RELEASE) {
                m_btn->setMode(MidButton::BtnMode::NORMAL);
            }
        }
        switch (event) {
            case MineField::EVENT_FIELD_PRESSED:
                m_btn->setMode(MidButton::BtnMode::SURPEISED);
                return 1;
            case MineField::EVENT_FIELD_RELEASED:
                m_btn->setMode(MidButton::BtnMode::NORMAL);
                return 1;
            case MineField::EVENT_STATE_UPDATED:
                _updateDisplay();
                return 1;
        }
        return Fl_Window::handle(event);
    }

};

#endif
