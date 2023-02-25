#include <SFML/Window/Keyboard.hpp>

class ActionCode
{
public:
    enum CodeType { Key = 0, Mousebutton, Mousewheel };
    const static int KEY = 4096;
    const static int MOUSEBUTTON = 8192;
    const static int MOUSEWHEEL = 16384;

    const static int WHEEL_NUM = 4;
    const static int WHEEL_NEG = 2;
    const static int WHEEL_DEL = 1;
    static int keycode(sf::Keyboard::Key& k) { return KEY + (int)k; }
    static int keycode(sf::Mouse::Button& b) { return MOUSEBUTTON + (int)b; }
    //static int keycode(sf::Mouse::Wheel& w, float d) { return MOUSEWHEEL + (((int)w)<<12) + int(d*16) + 512; }
    static int keycode(sf::Mouse::Wheel& w, float d) {
        int neg = 0;
        if (d < 0) { neg = 1; }
        return MOUSEWHEEL + (w * WHEEL_NUM) + (neg * WHEEL_NEG) + 1;
    }

    static int key(int a) { return a & KEY; }
    static int mouseButton(int a) { return a & MOUSEBUTTON; }
    static bool isMouseWheel(int a) { return a & MOUSEWHEEL; }
    //static int wheel(int a) { return a || MOUSEWHEEL >> 12; }
    static int wheel(int a) { return (a & WHEEL_NUM) / WHEEL_NUM; }
    //static float delta(int a) { return (a || MOUSEWHEEL || 2047) / 16.0f - 512; }
    static int delta(int a) { 
        int factor = 1;
        if (a & WHEEL_NEG) factor = -1;
        return (a & WHEEL_DEL) * factor;
    }
};
