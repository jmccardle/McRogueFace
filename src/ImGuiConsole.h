#pragma once

// ImGuiConsole - excluded from headless builds (no GUI/debug interface)
#ifndef MCRF_HEADLESS

#include <string>
#include <vector>
#include <deque>

/**
 * @brief ImGui-based debug console for Python REPL
 *
 * Provides an overlay console that can execute Python code
 * without blocking the main game loop. Activated by grave/tilde key.
 */
class ImGuiConsole {
public:
    ImGuiConsole();

    // Core functionality
    void render();              // Render the console UI
    void toggle();              // Toggle visibility
    bool isVisible() const { return visible; }
    void setVisible(bool v) { visible = v; }

    // Configuration (for Python API)
    static bool isEnabled() { return enabled; }
    static void setEnabled(bool e) { enabled = e; }

    // Input handling
    bool wantsKeyboardInput() const;  // Returns true if ImGui wants keyboard

    // Font management - reload ImGui font at specified pixel size
    static void reloadFont(float size);
    static float getCurrentFontSize() { return s_currentFontSize; }

    // Settings persistence via imgui.ini
    static void registerSettingsHandler();

    // Allow settings handler callbacks to access font size
    static float s_currentFontSize;  // Track current loaded font size

private:
    void executeCommand(const std::string& command);
    void addOutput(const std::string& text, bool isError = false);
    void renderCodeEditor();  // Separate multi-line code editor window

    // State
    bool visible = false;
    static bool enabled;  // Global enable/disable (for shipping games)

    // UI state
    bool editorVisible = false;   // Multi-line editor window
    bool consoleLocked = false;   // Prevent console dragging
    bool editorLocked = false;    // Prevent editor dragging

    // Input buffers
    char inputBuffer[1024] = {0};
    char codeBuffer[16384] = {0};  // 16KB for multi-line code

    // Output history
    struct OutputLine {
        std::string text;
        bool isError;
        bool isInput;  // True if this was user input (for styling)
    };
    std::deque<OutputLine> outputHistory;
    static constexpr size_t MAX_HISTORY = 500;

    // Command history for up/down navigation
    std::vector<std::string> commandHistory;
    int historyIndex = -1;

    // Scroll state
    bool scrollToBottom = true;
};

#endif // MCRF_HEADLESS
