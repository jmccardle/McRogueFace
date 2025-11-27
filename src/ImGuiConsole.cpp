#include "ImGuiConsole.h"
#include "imgui.h"
#include "McRFPy_API.h"
#include <Python.h>
#include <sstream>

// Static member initialization
bool ImGuiConsole::enabled = true;

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

    // Set up console window
    ImGuiIO& io = ImGui::GetIO();
    ImGui::SetNextWindowSize(ImVec2(io.DisplaySize.x, io.DisplaySize.y * 0.4f), ImGuiCond_FirstUseEver);
    ImGui::SetNextWindowPos(ImVec2(0, 0), ImGuiCond_FirstUseEver);

    ImGuiWindowFlags flags = ImGuiWindowFlags_NoCollapse;

    if (!ImGui::Begin("Console", &visible, flags)) {
        ImGui::End();
        return;
    }

    // Output area (scrollable, no horizontal scrollbar - use word wrap)
    float footerHeight = ImGui::GetStyle().ItemSpacing.y + ImGui::GetFrameHeightWithSpacing();
    ImGui::BeginChild("ScrollingRegion", ImVec2(0, -footerHeight), false, ImGuiWindowFlags_None);

    // Render output lines with word wrap
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

    // Keep focus on input
    ImGui::SetItemDefaultFocus();
    if (reclaimFocus || (visible && !ImGui::IsAnyItemActive())) {
        ImGui::SetKeyboardFocusHere(-1);
    }

    ImGui::End();
}
