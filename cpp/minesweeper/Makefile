CXX = g++

FLTKCXXFLAGS += $(shell fltk-config --cxxflags)
FLTKLDFLAGS += $(shell fltk-config --ldstaticflags)

CXXFLAGS += -std=c++17
CXXFLAGS += -Wall -Weffc++ -Wextra -Wpedantic -Wnon-virtual-dtor -Wshadow -pedantic-errors
STATICCXXFLAGS += -Os -s
STATICCXXFLAGS += -static
STATICCXXFLAGS += -fno-rtti -fno-exceptions
STATICLDFLAGS += -Wl,-as-needed

TARGET = minesweeper

.PHONY: build debug static clean

static: CXXFLAGS := $(FLTKCXXFLAGS) $(CXXFLAGS) $(STATICCXXFLAGS) 
static: LDFLAGS := $(FLTKLDFLAGS) $(LDFLAGS) $(STATICLDFLAGS)
static: $(TARGET)

build: CXXFLAGS := $(FLTKCXXFLAGS) $(CXXFLAGS)
build: LDFLAGS := $(FLTKLDFLAGS) $(LDFLAGS)
build: $(TARGET)

$(TARGET): $(TARGET).cpp
	$(CXX) -o $@ $^ $(CXXFLAGS) $(LDFLAGS)

debug: CXXFLAGS := $(CXXFLAGS) -DDEBUG -g -Og -lfltk
debug: $(TARGET).cpp
	$(CXX) -o $(TARGET) $^ $(CXXFLAGS) $(LDFLAGS)

clean:
	rm $(TARGET)

