CXX = g++

CXXFLAGS += $(shell fltk-config --cxxflags)
LDFLAGS += $(shell fltk-config --ldstaticflags)

CXXFLAGS += -std=c++17
CXXFLAGS += -Wall -Weffc++ -Wextra -Wsign-conversion -pedantic-errors
CXXFLAGS += -Os -s
CXXFLAGS += -static
CXXFLAGS += -fno-rtti -fno-exceptions
LDFLAGS += -Wl,-as-needed

TARGET = cfrs

$(TARGET): $(TARGET).cpp
	$(CXX) -o $@ $^ $(CXXFLAGS) $(LDFLAGS)

.PHONY: test clean
test:
	# offical demos
	./$(TARGET) ]
	./$(TARGET) [[[[[[[[[[[[[[[FF]]]]C]]]SRRF[RRR]F]]]]]]]]
	./$(TARGET) R[[[[[[[[[[[[[[FF]]]]]]]RRF[RRR]SC]]]]]]]
	./$(TARGET) [[[[[[[[[[[[[[[FF]]]]]]]SRRF[RRR]]]]]]C]]]
	./$(TARGET) [[[[[[[[[[[[[[F]]]]RCC]]]SRR[FFF][RRR][FF]]]]]]]]
	./$(TARGET) [[[[[[[[[[[[FF]]]]RR]][[[FFF]]]SRR[[F]][RRR]CC]]]]]]
	./$(TARGET) [[[[[[[[[[[[[[[FF]]]]RR]][[[FFF]]]RR[[F]][RRR]CC]]S]]]]R]]]

clean:
	rm $(TARGET)

