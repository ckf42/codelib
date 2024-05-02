#ifndef MineField_h
#define MineField_h

#ifdef DEBUG
#include <iostream>
#endif
#include <climits>
#include <random>
#include <stack>
#include <string>
#include <Fl/Fl.H>
#include <FL/Enumerations.H>
#include <FL/names.H>
#include <Fl/Fl_Button.H>
#include <Fl/Fl_Group.H>
#include <Fl/Fl_Window.H>

class MineTile : public Fl_Button {
private:
    inline void _showLabel(void) {
        if (m_hasMine) {
            this->copy_label("\U0001F4A3");  // bomb
        } else if (m_nearbyMineCount != 0) {
            this->labelfont(FL_HELVETICA_BOLD);
            this->labelsize(16);
            this->copy_label(std::to_string(m_nearbyMineCount).c_str());
            this->labelcolor(digitColor[m_nearbyMineCount]);
        }
        this->redraw_label();
    }

public:
    constexpr static int TILE_SIZE = 16;
    constexpr static Fl_Color digitColor[9] = {
        FL_BACKGROUND2_COLOR, 0x2A2AFF00, 0x00800000,
        0xff000000, 0x00008000, 0x80000000,
        0x00808000, 0x08080800, 0x80808000
    };

    enum struct TileState {
        HIDDEN,
        OPENED,
        FLAGED
    } m_state;
    bool m_hasMine;
    uint8_t m_nearbyMineCount, m_nearbyFlagCount;

    MineTile(int x, int y):
        Fl_Button(x, y, TILE_SIZE, TILE_SIZE, nullptr),
        m_state(TileState::HIDDEN), m_hasMine(false),
        m_nearbyMineCount(0), m_nearbyFlagCount(0) {};


    bool openTile(void) {
        // returns if opened a block with mine
        if (m_state != TileState::HIDDEN) {
            return false;
        }
        m_state = TileState::OPENED;
        this->set();
        this->_showLabel();
        return m_hasMine;
    }

    inline void toggleFlag(void) {
        switch (m_state) {
            case TileState::FLAGED:
                m_state = TileState::HIDDEN;
                this->copy_label("");
                this->redraw_label();
                break;
            case TileState::HIDDEN:
                m_state = TileState::FLAGED;
                this->copy_label("\U0001F6A9");  // trig flag, red in some sys?
                this->redraw_label();
                break;
            case TileState::OPENED:
            default:
                break;
        }
    }

    // never catch event
    inline int handle(int) {
        return 0;
    }

};

class MineField : public Fl_Group {
public:
    enum struct GameState {
        ACTIVE,
        WON,
        DEAD
    };

    static constexpr int EVENT_STATE_UPDATED = 419;  // Expired
    static constexpr int EVENT_FIELD_PRESSED = 420;
    static constexpr int EVENT_FIELD_RELEASED = 421;

private:
    // do not want to #include <algorithm> for this
    inline static constexpr int _capVal(int val, int minval = INT_MIN, int maxval = INT_MAX) {
        return (val < minval) ? minval : ((val > maxval) ? maxval : val);
    }

    int m_wCount, m_hCount, m_mineCount, m_remainHiddenCount, m_flagCount;
    int m_prevMouseI, m_prevMouseJ, m_prevMouseState;
    bool m_isGameStarted, m_ignoreNextRelease;
    GameState  m_state;

    // do not want to include <tuple> or <utility> for pair
    struct _GridCoor {
        int i, j;
        _GridCoor(int ii, int jj): i(ii), j(jj) {}
    };

    inline static bool _bernoulliTrial(int p, int q, std::mt19937 &randSource) {
        // probability p / q
        if (q <= 1) {
            return p >= q;
        }
        return std::uniform_int_distribution<int>(1, q)(randSource) <= p;
    }

    // https://stackoverflow.com/a/2938589
    template <typename Func>
    inline void _onNearbyIndices(int i, int j, Func op, int halfSize = 1) {
        for (int di = -halfSize; di <= halfSize; ++di) {
            if (i + di < 0 || i + di >= m_wCount) {
                continue;
            }
            for (int dj = -halfSize; dj <= halfSize; ++dj) {
                if (j + dj < 0 || j + dj >= m_hCount) {
                    continue;
                }
                op(i + di, j + dj);
            }
        }
    }

    void _moveMine(int i, int j) {
        if (m_isGameStarted || !_tile(i, j).m_hasMine) {
            return;
        }
        for (int idx = 0; idx < m_wCount * m_hCount; ++idx) {
            if (!_tile(idx).m_hasMine) {
                _tile(idx).m_hasMine = true;
                _onNearbyIndices(_toGridI(idx), _toGridJ(idx), [this](int ii, int jj) {
                    ++_tile(ii, jj).m_nearbyMineCount;
                });
#ifdef DEBUG
                tile(idx).copy_label("x");
                std::printf("moving mine from (%d, %d) to (%d, %d)\n",
                        i, j, toGridI(idx), toGridJ(idx));
#endif
                break;
            }
        }
        _tile(i, j).m_hasMine = false;
#ifdef DEBUG
        tile(i, j).copy_label("");
#endif
        _onNearbyIndices(i, j, [this](int ii, int jj){
            --_tile(ii, jj).m_nearbyMineCount;
        });
    }

    inline int _toTileIdx(int i, int j) const {
        return j * m_wCount + i;
    }

    inline int _toGridI(int idx) const {
        return idx % m_wCount;
    }

    inline int _toGridJ(int idx) const {
        return idx / m_wCount;
    }

    inline MineTile& _tile(int idx) const {
        return *reinterpret_cast<MineTile *>(child(idx));
    }

    inline MineTile& _tile(int i, int j) const {
        return _tile(_toTileIdx(i, j));
    }

    inline bool _isTileInbound(int i, int j) const {
        return i >= 0 && i < m_wCount && j >= 0 && j < m_hCount;
    }

public:
    MineField(
            int x, int y,
            int wCount = 9, int hCount = 9, int mineCount = 10):
        // NOTE: XP minesweeper cap size
        Fl_Group(x, y,
                MineTile::TILE_SIZE * _capVal(wCount, 9, 30),
                MineTile::TILE_SIZE * _capVal(hCount, 9, 24)),
        m_wCount(_capVal(wCount, 9, 30)),
        m_hCount(_capVal(hCount, 9, 24)),
        m_mineCount(0), m_remainHiddenCount(0), m_flagCount(0),
        m_prevMouseI(-1), m_prevMouseJ(-1), m_prevMouseState(0),
        m_isGameStarted(false), m_ignoreNextRelease(false), m_state(GameState::ACTIVE) {
        this->begin();
            for (int j = 0; j < m_hCount; ++j) {
                for (int i = 0; i < m_wCount; ++i) {
                    add(new MineTile(
                                this->x() + MineTile::TILE_SIZE * i,
                                this->y() + MineTile::TILE_SIZE * j));
                }
            }
        this->end();
        m_remainHiddenCount = m_wCount * m_hCount;
        // NOTE: XP minesweeper cap mine as follows
        m_mineCount = _capVal(mineCount, 10, (m_wCount - 1) * (m_hCount - 1));
        // decide where to put mines
        // https://stackoverflow.com/a/311716
        std::random_device dev;
        std::mt19937 ranGen(dev());
        int population = m_wCount * m_hCount, chosenCount = 0;
        for (int tileIdx = 0; tileIdx < population; ++tileIdx) {
            if (m_mineCount <= chosenCount) {
                break;
            }
            if (_bernoulliTrial(m_mineCount - chosenCount, population - tileIdx, ranGen)) {
                ++chosenCount;
                _tile(tileIdx).m_hasMine = true;
                int i = _toGridI(tileIdx), j = _toGridJ(tileIdx);
#ifdef DEBUG
                tile(tileIdx).copy_label("x");
#endif
                _onNearbyIndices(i, j, [this](int ii, int jj) {
                    ++_tile(ii, jj).m_nearbyMineCount;
                });
            }
        }
    }

    inline GameState getGameState(void) const {
        return m_state;
    }

    inline bool isGameStarted(void) const {
        return m_isGameStarted;
    }

    inline int getWCount(void) const {
        return m_wCount;
    }

    inline int getHCount(void) const {
        return m_hCount;
    }

    inline int getMineCount(void) const {
        return m_mineCount;
    }

    inline int getFlagCount(void) const {
        return m_flagCount;
    }

    inline void setBlockVal(int i, int j, int val, bool isLargeBlock) {
        _onNearbyIndices(i, j, [this, val](int ii, int jj) {
            if (_tile(ii, jj).m_state == MineTile::TileState::HIDDEN) {
#ifdef DEBUG
                std::printf("set (%d, %d) to %d\n", ii, jj, val);
#endif
                _tile(ii, jj).value(val);
            }
        }, isLargeBlock ? 1 : 0);
    }

    void openBlock(int i, int j, bool isLargeBlock) {
        std::stack<_GridCoor> ptsToOpen;
        _onNearbyIndices(i, j, [this, &ptsToOpen](int ii, int jj) {
            if (_tile(ii, jj).m_state == MineTile::TileState::HIDDEN) {
                _moveMine(ii, jj);
                ptsToOpen.emplace(ii, jj);
            }
        // m_isGameStarted should be true if isLargeBlock is true, but just to make sure
        }, (m_isGameStarted && isLargeBlock) ? 1 : 0);
#ifdef DEBUG
        std::printf("stack size: %lld\n", ptsToOpen.size());
#endif
        while (!ptsToOpen.empty()) {
            _GridCoor coor = ptsToOpen.top();
            ptsToOpen.pop();
            MineTile &mTile = _tile(coor.i, coor.j);
            if (mTile.m_state != MineTile::TileState::HIDDEN) {
                continue;
            }
#ifdef DEBUG
            std::printf("opening (%d, %d)\n", coor.i, coor.j);
#endif
            if (mTile.openTile()) {
                mTile.selection_color(FL_RED);
                m_state = GameState::DEAD;
#ifdef DEBUG
            std::printf("dead\n");
#endif
                showAnswer();
                break;
            } else if (mTile.m_nearbyMineCount == 0) {
                _onNearbyIndices(coor.i, coor.j, [this, &ptsToOpen](int ii, int jj) {
                    if (_tile(ii, jj).m_state == MineTile::TileState::HIDDEN) {
                        ptsToOpen.emplace(ii, jj);
                    }
                });
            }
            --m_remainHiddenCount;
#ifdef DEBUG
            std::printf("remainHiddenCount=%d\n", m_remainHiddenCount);
#endif
        }
        if (m_state == GameState::ACTIVE
                && m_remainHiddenCount <= m_mineCount) {  // this should not go below, but anyway
#ifdef DEBUG
            std::printf("board cleared\n");
#endif
            m_state = GameState::WON;
            showAnswer();
            m_flagCount = m_mineCount;
        }
    }

    // returns if flag count changes
    inline bool toggleFlag(int i, int j) {
        MineTile &mTile = _tile(i, j);
        if (mTile.m_state == MineTile::TileState::OPENED) {
            return false;
        }
        bool wasOnFlagged = mTile.m_state == MineTile::TileState::FLAGED;
        mTile.toggleFlag();
        _onNearbyIndices(i, j, [this, wasOnFlagged](int ii, int jj) {
            _tile(ii, jj).m_nearbyFlagCount += (wasOnFlagged ? -1 : 1);
        });
        m_flagCount += (wasOnFlagged ? -1 : 1);
#ifdef DEBUG
        std::printf(
                "toggled flag at (%d, %d), originally %d, now %d flags\n",
                i, j, wasOnFlagged, m_flagCount);
#endif
        return true;
    }

    inline void showAnswer(void) const {
#ifdef DEBUG
        std::printf("showing answers\n");
#endif
        for (int idx = 0; idx < m_wCount * m_hCount; ++idx) {
            MineTile &mTile = _tile(idx);
            if (mTile.m_hasMine) {
                if (m_state == MineField::GameState::WON
                        && mTile.m_state == MineTile::TileState::HIDDEN) {
                    mTile.toggleFlag();
                } else {
                    mTile.openTile();
                }
            } else if (mTile.m_state == MineTile::TileState::FLAGED) {
                // must have no mine
                mTile.copy_label("\u274C");  // cross mark
                mTile.redraw_label();
            }
        }
    }

    int handle(int event) {
        if (m_state != GameState::ACTIVE) {
            // just consume
            switch (event) {
                case FL_PUSH:
                case FL_RELEASE:
                case FL_DRAG:
                    return 1;
            }
            return Fl_Group::handle(event);
        }
        // trigger midButton label change
        if (event == FL_PUSH && Fl::event_button1() != 0) {
            this->parent()->handle(EVENT_FIELD_PRESSED);
        } else if (event == FL_RELEASE) {
            this->parent()->handle(EVENT_FIELD_RELEASED);
        }
        int mi = (Fl::event_x() - this->x()) / MineTile::TILE_SIZE,
            mj = (Fl::event_y() - this->y()) / MineTile::TILE_SIZE,
            currMouseState = Fl::event_buttons();
#ifdef DEBUG
        std::printf(
                "%s, (%d, %d), mouse = %d%d, prev (%d, %d), mouse = %d%d\n",
                (event == EVENT_STATE_UPDATED ? "EVENT_STATE_UPDATED" : fl_eventnames[event]),
                mi, mj,
                (currMouseState & FL_BUTTON1) != 0, (currMouseState & FL_BUTTON3) != 0,
                m_prevMouseI, m_prevMouseJ,
                (m_prevMouseState & FL_BUTTON1) != 0, (m_prevMouseState & FL_BUTTON3) != 0);
#endif
        switch (event) {
            case FL_PUSH:  // mouse down
                // X -> L:
                // tile down
                // X -> R:
                // place flag
                // L / R -> LR:
                // tile down 3x3
                m_ignoreNextRelease = false;
                switch (currMouseState) {
                    case FL_BUTTON1:
                        setBlockVal(mi, mj, 1, false);
                        break;
                    case FL_BUTTON3:
                        if (toggleFlag(mi, mj)) {
                            this->parent()->handle(EVENT_STATE_UPDATED);
                        }
                        break;
                    case FL_BUTTON1 | FL_BUTTON3:
                        setBlockVal(mi, mj, 1, true);
                        break;
                    default:
                        break;
                }
                m_prevMouseI = mi;
                m_prevMouseJ = mj;
                m_prevMouseState = currMouseState;
                return 1;
                break;
            case FL_RELEASE:  // mouse up
                // L -> X:
                // open tile
                // R -> X:
                // nop
                // LR -> L / R:
                // (if tile full flag) quick open 3x3, block next release
                // (else) tile up 3x3
                if (m_ignoreNextRelease) {
                    m_prevMouseState = currMouseState;
                    m_ignoreNextRelease = false;
                    return 1;
                }
                switch (m_prevMouseState) {
                    case FL_BUTTON1:
                        openBlock(mi, mj, false);
                        m_isGameStarted = true;
                        this->parent()->handle(EVENT_STATE_UPDATED);
                        break;
                    case FL_BUTTON3:
                        break;
                    case FL_BUTTON1 | FL_BUTTON3:
                        if (_isTileInbound(mi, mj)
                                && _tile(mi, mj).m_state == MineTile::TileState::OPENED
                                && _tile(mi, mj).m_nearbyMineCount != 0
                                && _tile(mi, mj).m_nearbyFlagCount == _tile(mi, mj).m_nearbyMineCount) {
                            openBlock(mi, mj, true);
                            this->parent()->handle(EVENT_STATE_UPDATED);
                        } else {
                            setBlockVal(mi, mj, 0, true);
                        }
                        m_ignoreNextRelease = true;
                        break;
                    default:
                        break;
                }
                m_prevMouseState = currMouseState;
                return 1;
                break;
            case FL_DRAG:  // mouse move with key down
                // L / LR:
                // down tile move
                // R:
                // nop
                if (currMouseState & FL_BUTTON1) {
                    if (currMouseState & FL_BUTTON3) {
                        setBlockVal(m_prevMouseI, m_prevMouseJ, 0, true);
                        setBlockVal(mi, mj, 1, true);
                    } else {
                        setBlockVal(m_prevMouseI, m_prevMouseJ, 0, false);
                        setBlockVal(mi, mj, 1, false);
                    }
                }
                m_prevMouseI = mi;
                m_prevMouseJ = mj;
                return 1;
                break;
            default:
                return Fl_Group::handle(event);
        }
        return 0;
    }

#ifdef DEBUG
    ~MineField() {
        std::printf("Deleting minefield (%d x %d, %d)\n", m_wCount, m_hCount, m_mineCount);
    }
#endif

};

#endif
