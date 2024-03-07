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

    static std::string key_str(sf::Keyboard::Key& keycode)
    {
        switch(keycode)
        {
            case sf::Keyboard::Key::Unknown: return "Unknown"; break;
            case sf::Keyboard::Key::A: return "A"; break;
            case sf::Keyboard::Key::B: return "B"; break;
            case sf::Keyboard::Key::C: return "C"; break;
            case sf::Keyboard::Key::D: return "D"; break;
            case sf::Keyboard::Key::E: return "E"; break;
            case sf::Keyboard::Key::F: return "F"; break;
            case sf::Keyboard::Key::G: return "G"; break;
            case sf::Keyboard::Key::H: return "H"; break;
            case sf::Keyboard::Key::I: return "I"; break;
            case sf::Keyboard::Key::J: return "J"; break;
            case sf::Keyboard::Key::K: return "K"; break;
            case sf::Keyboard::Key::L: return "L"; break;
            case sf::Keyboard::Key::M: return "M"; break;
            case sf::Keyboard::Key::N: return "N"; break;
            case sf::Keyboard::Key::O: return "O"; break;
            case sf::Keyboard::Key::P: return "P"; break;
            case sf::Keyboard::Key::Q: return "Q"; break;
            case sf::Keyboard::Key::R: return "R"; break;
            case sf::Keyboard::Key::S: return "S"; break;
            case sf::Keyboard::Key::T: return "T"; break;
            case sf::Keyboard::Key::U: return "U"; break;
            case sf::Keyboard::Key::V: return "V"; break;
            case sf::Keyboard::Key::W: return "W"; break;
            case sf::Keyboard::Key::X: return "X"; break;
            case sf::Keyboard::Key::Y: return "Y"; break;
            case sf::Keyboard::Key::Z: return "Z"; break;
            case sf::Keyboard::Key::Num0: return "Num0"; break;
            case sf::Keyboard::Key::Num1: return "Num1"; break;
            case sf::Keyboard::Key::Num2: return "Num2"; break;
            case sf::Keyboard::Key::Num3: return "Num3"; break;
            case sf::Keyboard::Key::Num4: return "Num4"; break;
            case sf::Keyboard::Key::Num5: return "Num5"; break;
            case sf::Keyboard::Key::Num6: return "Num6"; break;
            case sf::Keyboard::Key::Num7: return "Num7"; break;
            case sf::Keyboard::Key::Num8: return "Num8"; break;
            case sf::Keyboard::Key::Num9: return "Num9"; break;
            case sf::Keyboard::Key::Escape: return "Escape"; break;
            case sf::Keyboard::Key::LControl: return "LControl"; break;
            case sf::Keyboard::Key::LShift: return "LShift"; break;
            case sf::Keyboard::Key::LAlt: return "LAlt"; break;
            case sf::Keyboard::Key::LSystem: return "LSystem"; break;
            case sf::Keyboard::Key::RControl: return "RControl"; break;
            case sf::Keyboard::Key::RShift: return "RShift"; break;
            case sf::Keyboard::Key::RAlt: return "RAlt"; break;
            case sf::Keyboard::Key::RSystem: return "RSystem"; break;
            case sf::Keyboard::Key::Menu: return "Menu"; break;
            case sf::Keyboard::Key::LBracket: return "LBracket"; break;
            case sf::Keyboard::Key::RBracket: return "RBracket"; break;
            case sf::Keyboard::Key::Semicolon: return "Semicolon"; break;
            case sf::Keyboard::Key::Comma: return "Comma"; break;
            case sf::Keyboard::Key::Period: return "Period"; break;
            case sf::Keyboard::Key::Apostrophe: return "Apostrophe"; break;
            case sf::Keyboard::Key::Slash: return "Slash"; break;
            case sf::Keyboard::Key::Backslash: return "Backslash"; break;
            case sf::Keyboard::Key::Grave: return "Grave"; break;
            case sf::Keyboard::Key::Equal: return "Equal"; break;
            case sf::Keyboard::Key::Hyphen: return "Hyphen"; break;
            case sf::Keyboard::Key::Space: return "Space"; break;
            case sf::Keyboard::Key::Enter: return "Enter"; break;
            case sf::Keyboard::Key::Backspace: return "Backspace"; break;
            case sf::Keyboard::Key::Tab: return "Tab"; break;
            case sf::Keyboard::Key::PageUp: return "PageUp"; break;
            case sf::Keyboard::Key::PageDown: return "PageDown"; break;
            case sf::Keyboard::Key::End: return "End"; break;
            case sf::Keyboard::Key::Home: return "Home"; break;
            case sf::Keyboard::Key::Insert: return "Insert"; break;
            case sf::Keyboard::Key::Delete: return "Delete"; break;
            case sf::Keyboard::Key::Add: return "Add"; break;
            case sf::Keyboard::Key::Subtract: return "Subtract"; break;
            case sf::Keyboard::Key::Multiply: return "Multiply"; break;
            case sf::Keyboard::Key::Divide: return "Divide"; break;
            case sf::Keyboard::Key::Left: return "Left"; break;
            case sf::Keyboard::Key::Right: return "Right"; break;
            case sf::Keyboard::Key::Up: return "Up"; break;
            case sf::Keyboard::Key::Down: return "Down"; break;
            case sf::Keyboard::Key::Numpad0: return "Numpad0"; break;
            case sf::Keyboard::Key::Numpad1: return "Numpad1"; break;
            case sf::Keyboard::Key::Numpad2: return "Numpad2"; break;
            case sf::Keyboard::Key::Numpad3: return "Numpad3"; break;
            case sf::Keyboard::Key::Numpad4: return "Numpad4"; break;
            case sf::Keyboard::Key::Numpad5: return "Numpad5"; break;
            case sf::Keyboard::Key::Numpad6: return "Numpad6"; break;
            case sf::Keyboard::Key::Numpad7: return "Numpad7"; break;
            case sf::Keyboard::Key::Numpad8: return "Numpad8"; break;
            case sf::Keyboard::Key::Numpad9: return "Numpad9"; break;
            case sf::Keyboard::Key::F1: return "F1"; break;
            case sf::Keyboard::Key::F2: return "F2"; break;
            case sf::Keyboard::Key::F3: return "F3"; break;
            case sf::Keyboard::Key::F4: return "F4"; break;
            case sf::Keyboard::Key::F5: return "F5"; break;
            case sf::Keyboard::Key::F6: return "F6"; break;
            case sf::Keyboard::Key::F7: return "F7"; break;
            case sf::Keyboard::Key::F8: return "F8"; break;
            case sf::Keyboard::Key::F9: return "F9"; break;
            case sf::Keyboard::Key::F10: return "F10"; break;
            case sf::Keyboard::Key::F11: return "F11"; break;
            case sf::Keyboard::Key::F12: return "F12"; break;
            case sf::Keyboard::Key::F13: return "F13"; break;
            case sf::Keyboard::Key::F14: return "F14"; break;
            case sf::Keyboard::Key::F15: return "F15"; break;
            case sf::Keyboard::Key::Pause: return "Pause"; break;
        default:
            return "Any";
            break;
        }
    }
};
