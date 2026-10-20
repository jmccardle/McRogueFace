#ifndef MCROGUEFACE_CONFIG_H
#define MCROGUEFACE_CONFIG_H

#include <string>
#include <vector>
#include <filesystem>

struct McRogueFaceConfig {
    // McRogueFace specific
    bool headless = false;
    bool audio_enabled = true;
    bool audio_explicit = false;  // --audio-on/--audio-off given: --headless must not override it
    
    // Python interpreter emulation
    bool python_mode = false;
    bool plain_interpreter = false;  // launched as python*: a script runs headless and exits (#505)
    std::string python_command;      // -c command
    std::string python_module;       // -m module
    bool interactive_mode = false;   // -i flag
    bool show_version = false;       // -V flag
    bool show_help = false;          // -h flag
    
    // CPython interpreter flags (#505). Each maps to the PyConfig field of the same
    // meaning, and reaches both interpreter init paths (-c/-m/--exec and the game).
    bool isolated = false;           // -I  PyConfig.isolated
    bool ignore_environment = false; // -E  PyConfig.use_environment = 0
    bool no_user_site = false;       // -s  PyConfig.user_site_directory = 0
    bool no_site = false;            // -S  PyConfig.site_import = 0
    bool dont_write_bytecode = false;// -B  PyConfig.write_bytecode = 0
    bool unbuffered = false;         // -u  PyConfig.buffered_stdio = 0
    bool quiet = false;              // -q  PyConfig.quiet
    int verbose = 0;                 // -v  PyConfig.verbose (repeatable)
    int optimize = 0;                // -O  PyConfig.optimization_level (-OO = 2)
    std::vector<std::string> warnoptions;  // -W arg  PyConfig.warnoptions
    std::vector<std::string> xoptions;     // -X opt  PyConfig.xoptions

    // argv[0] exactly as the process was launched (#505). The engine hands CPython the
    // unresolved path built from it, so a venv's bin/python symlink is found the way
    // CPython finds it. Empty when nothing set it (tests building a config by hand).
    std::string launch_argv0;

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

    // --use-virtual-env: honour VIRTUAL_ENV even in a packaged game (#510)
    bool use_virtual_env = false;
};

#endif // MCROGUEFACE_CONFIG_H