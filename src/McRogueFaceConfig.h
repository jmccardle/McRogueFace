#ifndef MCROGUEFACE_CONFIG_H
#define MCROGUEFACE_CONFIG_H

#include <string>
#include <vector>
#include <filesystem>

struct McRogueFaceConfig {
    // McRogueFace specific
    bool headless = false;
    bool audio_enabled = true;
    
    // Python interpreter emulation
    bool python_mode = false;
    std::string python_command;      // -c command
    std::string python_module;       // -m module
    bool interactive_mode = false;   // -i flag
    bool show_version = false;       // -V flag
    bool show_help = false;          // -h flag
    
    // Script execution
    std::filesystem::path script_path;
    std::vector<std::string> script_args;
    
    // Scripts to execute before main script (--exec flag)
    std::vector<std::filesystem::path> exec_scripts;
    
    // Screenshot functionality for headless mode
    std::string screenshot_path;
    bool take_screenshot = false;

    // Auto-exit when no timers remain (for --headless --exec automation)
    bool auto_exit_after_exec = false;

    // Keep running after --exec scripts finish, instead of exiting (#350).
    // Headless --exec normally exits when the scripts are done: step() is the only
    // headless clock, so the engine cannot advance timers on its own and would
    // otherwise spin forever. Pass --run-forever for a long-lived headless process
    // (a server, a REPL host) that drives itself.
    bool run_forever = false;

    // Exception handling: exit on first Python callback exception (default: true)
    // Use --continue-after-exceptions to disable
    bool exit_on_exception = true;
};

#endif // MCROGUEFACE_CONFIG_H