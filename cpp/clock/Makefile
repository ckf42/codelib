CXX = g++

CXXFLAGS += $(shell fltk-config --cxxflags)
LDFLAGS += $(shell fltk-config --ldstaticflags)

CXXFLAGS += -std=c++17
CXXFLAGS += -Wall -Weffc++ -Wextra -Wsign-conversion -pedantic-errors
CXXFLAGS += -Os -s
CXXFLAGS += -static
CXXFLAGS += -fno-rtti -fno-exceptions
LDFLAGS += -Wl,-as-needed

clock: clock.cpp
	$(CXX) -o $@ $^ $(CXXFLAGS) $(LDFLAGS)

clean:
	rm -f clock

