// ImGuiConsole.cpp - Debug console using ImGui
// This file is excluded from headless builds (no GUI/debug interface needed)

#ifndef MCRF_HEADLESS

#include "ImGuiConsole.h"
#include "imgui.h"
#include "imgui_internal.h"  // For ImGuiSettingsHandler, ImHashStr, MarkIniSettingsDirty
#include "imgui-SFML.h"
#include "McRFPy_API.h"
#include <Python.h>
#include <sstream>
#include <algorithm>
#include <cstring>

// Static member initialization
bool ImGuiConsole::enabled = true;
float ImGuiConsole::s_currentFontSize = 16.0f;

void ImGuiConsole::reloadFont(float size) {
    // Clamp size to reasonable bounds
    size = std::max(8.0f, std::min(32.0f, size));

    ImGuiIO& io = ImGui::GetIO();

    // Clear existing fonts
    io.Fonts->Clear();

    // Load JetBrains Mono at the new size
    io.Fonts->AddFontFromFileTTF("./assets/JetbrainsMono.ttf", size);

    // Rebuild the font texture
    if (!ImGui::SFML::UpdateFontTexture()) {
        // Font texture update failed - revert to default
        io.Fonts->Clear();
        io.Fonts->AddFontDefault();
        (void)ImGui::SFML::UpdateFontTexture();  // Cast to void - can't fail on default font
        return;
    }

    s_currentFontSize = size;

    // Mark imgui.ini as dirty so font size gets saved
    ImGui::MarkIniSettingsDirty();
}

// Settings handler callbacks for imgui.ini persistence
static void* ConsoleSettingsHandler_ReadOpen(ImGuiContext*, ImGuiSettingsHandler*, const char* name) {
    // We only have one console, so just return a non-null pointer
    if (strcmp(name, "Main") == 0) {
        return (void*)1;  // Non-null to indicate valid entry
    }
    return nullptr;
}

static void ConsoleSettingsHandler_ReadLine(ImGuiContext*, ImGuiSettingsHandler*, void* entry, const char* line) {
    float size;
    if (sscanf(line, "FontSize=%f", &size) == 1) {
        // Don't reload font here - just store the value
        // Font will be loaded after settings are applied
        ImGuiConsole::s_currentFontSize = std::max(8.0f, std::min(32.0f, size));
    }
}

static void ConsoleSettingsHandler_ApplyAll(ImGuiContext*, ImGuiSettingsHandler*) {
    // After all settings are read, reload the font at the saved size
    ImGuiConsole::reloadFont(ImGuiConsole::s_currentFontSize);
}

static void ConsoleSettingsHandler_WriteAll(ImGuiContext*, ImGuiSettingsHandler* handler, ImGuiTextBuffer* buf) {
    buf->appendf("[%s][Main]\n", handler->TypeName);
    buf->appendf("FontSize=%.0f\n", ImGuiConsole::s_currentFontSize);
    buf->append("\n");
}

void ImGuiConsole::registerSettingsHandler() {
    ImGuiSettingsHandler ini_handler;
    ini_handler.TypeName = "Console";
    ini_handler.TypeHash = ImHashStr("Console");
    ini_handler.ReadOpenFn = ConsoleSettingsHandler_ReadOpen;
    ini_handler.ReadLineFn = ConsoleSettingsHandler_ReadLine;
    ini_handler.ApplyAllFn = ConsoleSettingsHandler_ApplyAll;
    ini_handler.WriteAllFn = ConsoleSettingsHandler_WriteAll;
    ImGui::GetCurrentContext()->SettingsHandlers.push_back(ini_handler);
}

ImGuiConsole::ImGuiConsole() {
    addOutput("McRogueFace Python Console", false);
    addOutput("Type Python commands and press Enter to execute.", false);
    addOutput("", false);
}

void ImGuiConsole::toggle() {
    if (enabled) {
        visible = !visible;
        if (visible) {
            // Focus input when opening
            ImGui::SetWindowFocus("Console");
        }
    }
}

bool ImGuiConsole::wantsKeyboardInput() const {
    return visible && enabled;
}

void ImGuiConsole::addOutput(const std::string& text, bool isError) {
    // Split text by newlines and add each line separately
    std::istringstream stream(text);
    std::string line;
    while (std::getline(stream, line)) {
        outputHistory.push_back({line, isError, false});
    }

    // Trim history if too long
    while (outputHistory.size() > MAX_HISTORY) {
        outputHistory.pop_front();
    }

    scrollToBottom = true;
}

void ImGuiConsole::executeCommand(const std::string& command) {
    if (command.empty()) return;

    // Add command to output with >>> prefix
    outputHistory.push_back({">>> " + command, false, true});

    // Add to command history
    commandHistory.push_back(command);
    historyIndex = -1;

    // Capture Python output
    // Redirect stdout/stderr to capture output
    std::string captureCode = R"(
import sys
import io
_console_stdout = io.StringIO()
_console_stderr = io.StringIO()
_old_stdout = sys.stdout
_old_stderr = sys.stderr
sys.stdout = _console_stdout
sys.stderr = _console_stderr
)";

    std::string restoreCode = R"(
sys.stdout = _old_stdout
sys.stderr = _old_stderr
_stdout_val = _console_stdout.getvalue()
_stderr_val = _console_stderr.getvalue()
)";

    // Set up capture
    PyRun_SimpleString(captureCode.c_str());

    // Try to evaluate as expression first (for things like "2+2")
    PyObject* main_module = PyImport_AddModule("__main__");
    PyObject* main_dict = PyModule_GetDict(main_module);

    // First try eval (for expressions that return values)
    PyObject* result = PyRun_String(command.c_str(), Py_eval_input, main_dict, main_dict);
    bool showedResult = false;

    if (result == nullptr) {
        // Clear the error from eval attempt
        PyErr_Clear();

        // Try exec (for statements)
        result = PyRun_String(command.c_str(), Py_file_input, main_dict, main_dict);

        if (result == nullptr) {
            // Real error - capture it
            PyErr_Print();  // This prints to stderr which we're capturing
        }
    } else if (result != Py_None) {
        // Expression returned a non-None value - show its repr
        PyObject* repr = PyObject_Repr(result);
        if (repr) {
            const char* repr_str = PyUnicode_AsUTF8(repr);
            if (repr_str) {
                addOutput(repr_str, false);
                showedResult = true;
            }
            Py_DECREF(repr);
        }
    }
    Py_XDECREF(result);

    // Restore stdout/stderr
    PyRun_SimpleString(restoreCode.c_str());

    // Get captured stdout (only if we didn't already show a result)
    PyObject* stdout_val = PyObject_GetAttrString(main_module, "_stdout_val");
    if (stdout_val && PyUnicode_Check(stdout_val)) {
        const char* stdout_str = PyUnicode_AsUTF8(stdout_val);
        if (stdout_str && strlen(stdout_str) > 0) {
            addOutput(stdout_str, false);
        }
    }
    Py_XDECREF(stdout_val);

    // Get captured stderr
    PyObject* stderr_val = PyObject_GetAttrString(main_module, "_stderr_val");
    if (stderr_val && PyUnicode_Check(stderr_val)) {
        const char* stderr_str = PyUnicode_AsUTF8(stderr_val);
        if (stderr_str && strlen(stderr_str) > 0) {
            addOutput(stderr_str, true);
        }
    }
    Py_XDECREF(stderr_val);

    // Clean up temporary variables
    PyRun_SimpleString("del _console_stdout, _console_stderr, _old_stdout, _old_stderr, _stdout_val, _stderr_val");

    scrollToBottom = true;
}

void ImGuiConsole::render() {
    if (!visible || !enabled) return;

    // Render the code editor window if visible
    if (editorVisible) {
        renderCodeEditor();
    }

    // Set up console window
    ImGuiIO& io = ImGui::GetIO();
    ImGui::SetNextWindowSize(ImVec2(io.DisplaySize.x, io.DisplaySize.y * 0.4f), ImGuiCond_FirstUseEver);
    ImGui::SetNextWindowPos(ImVec2(0, 0), ImGuiCond_FirstUseEver);

    ImGuiWindowFlags flags = ImGuiWindowFlags_NoCollapse | ImGuiWindowFlags_MenuBar;
    if (consoleLocked) flags |= ImGuiWindowFlags_NoMove;

    if (!ImGui::Begin("Console", &visible, flags)) {
        ImGui::End();
        return;
    }

    // Menu bar with toolbar buttons
    if (ImGui::BeginMenuBar()) {
        // Font size controls (adjust by 2 pixels, reload font)
        // Use static s_currentFontSize since font is shared across all ImGui
        if (ImGui::SmallButton("-")) {
            float newSize = std::max(8.0f, s_currentFontSize - 2.0f);
            if (newSize != s_currentFontSize) {
                reloadFont(newSize);
            }
        }
        if (ImGui::IsItemHovered()) ImGui::SetTooltip("Decrease font size");

        ImGui::Text("%.0fpx", s_currentFontSize);

        if (ImGui::SmallButton("+")) {
            float newSize = std::min(32.0f, s_currentFontSize + 2.0f);
            if (newSize != s_currentFontSize) {
                reloadFont(newSize);
            }
        }
        if (ImGui::IsItemHovered()) ImGui::SetTooltip("Increase font size");

        ImGui::Separator();

        // Clear console output
        if (ImGui::SmallButton("Clr")) {
            outputHistory.clear();
        }
        if (ImGui::IsItemHovered()) ImGui::SetTooltip("Clear console output");

        // Send console output to code editor
        if (ImGui::SmallButton("Snd")) {
            // Build text from output history and copy to code editor
            std::string allOutput;
            for (const auto& line : outputHistory) {
                allOutput += line.text;
                allOutput += "\n";
            }
            // Copy to code editor buffer (truncate if too long)
            size_t copyLen = std::min(allOutput.size(), sizeof(codeBuffer) - 1);
            memcpy(codeBuffer, allOutput.c_str(), copyLen);
            codeBuffer[copyLen] = '\0';
            editorVisible = true;  // Show editor when sending
        }
        if (ImGui::IsItemHovered()) ImGui::SetTooltip("Send console output to code editor");

        ImGui::Separator();

        // Multi-line editor toggle
        if (ImGui::SmallButton("T")) {
            editorVisible = !editorVisible;
        }
        if (ImGui::IsItemHovered()) ImGui::SetTooltip("Toggle multi-line code editor");

        ImGui::Separator();

        // Lock/unlock toggle
        if (ImGui::SmallButton(consoleLocked ? "U" : "L")) {
            consoleLocked = !consoleLocked;
        }
        if (ImGui::IsItemHovered()) {
            ImGui::SetTooltip(consoleLocked ? "Unlock window movement" : "Lock window position");
        }

        ImGui::EndMenuBar();
    }

    // Output area (scrollable)
    float footerHeight = ImGui::GetStyle().ItemSpacing.y + ImGui::GetFrameHeightWithSpacing();
    ImGui::BeginChild("ScrollingRegion", ImVec2(0, -footerHeight), false, ImGuiWindowFlags_None);

    // Render output lines with color coding
    for (const auto& line : outputHistory) {
        if (line.isInput) {
            // User input - yellow/gold color
            ImGui::PushStyleColor(ImGuiCol_Text, ImVec4(1.0f, 0.9f, 0.4f, 1.0f));
        } else if (line.isError) {
            // Error - red color
            ImGui::PushStyleColor(ImGuiCol_Text, ImVec4(1.0f, 0.4f, 0.4f, 1.0f));
        } else {
            // Normal output - default color
            ImGui::PushStyleColor(ImGuiCol_Text, ImVec4(0.8f, 0.8f, 0.8f, 1.0f));
        }

        ImGui::TextWrapped("%s", line.text.c_str());
        ImGui::PopStyleColor();
    }

    // Auto-scroll to bottom when new content is added
    if (scrollToBottom || ImGui::GetScrollY() >= ImGui::GetScrollMaxY()) {
        ImGui::SetScrollHereY(1.0f);
    }
    scrollToBottom = false;

    ImGui::EndChild();

    // Input line
    ImGui::Separator();

    // Input field
    ImGuiInputTextFlags inputFlags = ImGuiInputTextFlags_EnterReturnsTrue |
                                      ImGuiInputTextFlags_CallbackHistory |
                                      ImGuiInputTextFlags_CallbackCompletion;

    bool reclaimFocus = false;

    // Custom callback for history navigation
    auto callback = [](ImGuiInputTextCallbackData* data) -> int {
        ImGuiConsole* console = static_cast<ImGuiConsole*>(data->UserData);

        if (data->EventFlag == ImGuiInputTextFlags_CallbackHistory) {
            if (console->commandHistory.empty()) return 0;

            if (data->EventKey == ImGuiKey_UpArrow) {
                if (console->historyIndex < 0) {
                    console->historyIndex = static_cast<int>(console->commandHistory.size()) - 1;
                } else if (console->historyIndex > 0) {
                    console->historyIndex--;
                }
            } else if (data->EventKey == ImGuiKey_DownArrow) {
                if (console->historyIndex >= 0) {
                    console->historyIndex++;
                    if (console->historyIndex >= static_cast<int>(console->commandHistory.size())) {
                        console->historyIndex = -1;
                    }
                }
            }

            // Update input buffer
            if (console->historyIndex >= 0 && console->historyIndex < static_cast<int>(console->commandHistory.size())) {
                const std::string& historyEntry = console->commandHistory[console->historyIndex];
                data->DeleteChars(0, data->BufTextLen);
                data->InsertChars(0, historyEntry.c_str());
            } else {
                data->DeleteChars(0, data->BufTextLen);
            }
        }

        return 0;
    };

    ImGui::PushItemWidth(-1);  // Full width
    if (ImGui::InputText("##Input", inputBuffer, sizeof(inputBuffer), inputFlags, callback, this)) {
        std::string command(inputBuffer);
        inputBuffer[0] = '\0';
        executeCommand(command);
        reclaimFocus = true;
    }
    ImGui::PopItemWidth();

    // Keep focus on input only after executing a command
    ImGui::SetItemDefaultFocus();
    if (reclaimFocus) {
        ImGui::SetKeyboardFocusHere(-1);
    }

    ImGui::End();
}

void ImGuiConsole::renderCodeEditor() {
    ImGuiIO& io = ImGui::GetIO();

    // Position editor below the console by default
    ImGui::SetNextWindowSize(ImVec2(io.DisplaySize.x * 0.6f, io.DisplaySize.y * 0.4f), ImGuiCond_FirstUseEver);
    ImGui::SetNextWindowPos(ImVec2(io.DisplaySize.x * 0.2f, io.DisplaySize.y * 0.45f), ImGuiCond_FirstUseEver);

    ImGuiWindowFlags flags = ImGuiWindowFlags_NoCollapse | ImGuiWindowFlags_MenuBar;
    if (editorLocked) flags |= ImGuiWindowFlags_NoMove;

    if (!ImGui::Begin("Code Editor", &editorVisible, flags)) {
        ImGui::End();
        return;
    }

    // Menu bar
    if (ImGui::BeginMenuBar()) {
        // Run button
        if (ImGui::SmallButton("Run") || (ImGui::IsWindowFocused(ImGuiFocusedFlags_ChildWindows) &&
                                           io.KeyCtrl && ImGui::IsKeyPressed(ImGuiKey_Enter))) {
            std::string code(codeBuffer);
            if (!code.empty()) {
                executeCommand(code);
            }
        }
        if (ImGui::IsItemHovered()) ImGui::SetTooltip("Execute code (Ctrl+Enter)");

        // Clear button
        if (ImGui::SmallButton("Clear")) {
            codeBuffer[0] = '\0';
        }
        if (ImGui::IsItemHovered()) ImGui::SetTooltip("Clear editor");

        ImGui::Separator();

        // Lock/unlock toggle
        if (ImGui::SmallButton(editorLocked ? "U" : "L")) {
            editorLocked = !editorLocked;
        }
        if (ImGui::IsItemHovered()) {
            ImGui::SetTooltip(editorLocked ? "Unlock window movement" : "Lock window position");
        }

        ImGui::EndMenuBar();
    }

    // Multi-line text input - fills available space
    ImVec2 contentSize = ImGui::GetContentRegionAvail();
    ImGuiInputTextFlags textFlags = ImGuiInputTextFlags_AllowTabInput;

    ImGui::InputTextMultiline("##CodeEditor", codeBuffer, sizeof(codeBuffer),
                               contentSize, textFlags);

    ImGui::End();
}

#endif // MCRF_HEADLESS
