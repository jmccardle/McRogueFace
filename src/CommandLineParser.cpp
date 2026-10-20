#include "CommandLineParser.h"
#include "Python.h"  // PY_VERSION, Py_GIL_DISABLED
#include <iostream>
#include <filesystem>
#include <algorithm>

CommandLineParser::CommandLineParser(int argc, char* argv[]) 
    : argc(argc), argv(argv) {}

CommandLineParser::ParseResult CommandLineParser::parse(McRogueFaceConfig& config) {
    ParseResult result;
    current_arg = 1;  // Reset for each parse
    if (argc > 0) config.launch_argv0 = argv[0];  // #505
    
    // Detect if running as Python interpreter
#ifndef __EMSCRIPTEN__
    std::filesystem::path exec_name = std::filesystem::path(argv[0]).filename();
    if (exec_name.string().find("python") == 0) {
        config.headless = true;
        config.python_mode = true;
        config.plain_interpreter = true;  // #505: a script runs and exits
    }
#endif
    
    while (current_arg < argc) {
        std::string arg = argv[current_arg];
        
        // Handle Python-style single-letter flags
        if (arg == "-h" || arg == "--help") {
            print_help();
            result.should_exit = true;
            result.exit_code = 0;
            return result;
        }
        
        if (arg == "-V" || arg == "--version") {
            print_version();
            result.should_exit = true;
            result.exit_code = 0;
            return result;
        }
        
        // Python execution modes
        if (arg == "-c") {
            config.python_mode = true;
            current_arg++;
            if (current_arg >= argc) {
                std::cerr << "Argument expected for the -c option" << std::endl;
                result.should_exit = true;
                result.exit_code = 1;
                return result;
            }
            config.python_command = argv[current_arg];
            current_arg++;
            continue;
        }
        
        if (arg == "-m") {
            config.python_mode = true;
            current_arg++;
            if (current_arg >= argc) {
                std::cerr << "Argument expected for the -m option" << std::endl;
                result.should_exit = true;
                result.exit_code = 1;
                return result;
            }
            config.python_module = argv[current_arg];
            current_arg++;
            // Collect remaining args as module args
            while (current_arg < argc) {
                config.script_args.push_back(argv[current_arg]);
                current_arg++;
            }
            continue;
        }
        
        if (arg == "-i") {
            config.interactive_mode = true;
            config.python_mode = true;
            current_arg++;
            continue;
        }
        
        // CPython interpreter flags (#505): -I -E -s -S -B -u -q -v -O (clusterable, as in
        // `python -Es`) and -W/-X, whose value is attached (-Wignore) or the next argument.
        if (arg.size() >= 2 && arg[0] == '-' && arg[1] != '-' &&
            std::string("IEsSBuqvOWX").find(arg[1]) != std::string::npos) {
            if (!parse_interpreter_flags(arg, config, result)) return result;
            continue;
        }

        // McRogueFace specific flags
        if (arg == "--headless") {
            config.headless = true;
            if (!config.audio_explicit) config.audio_enabled = false;
            current_arg++;
            continue;
        }
        
        if (arg == "--run-forever") {
            config.run_forever = true;
            current_arg++;
            continue;
        }

        if (arg == "--audio-off") {
            config.audio_enabled = false;
            config.audio_explicit = true;
            current_arg++;
            continue;
        }
        
        if (arg == "--audio-on") {
            config.audio_enabled = true;
            config.audio_explicit = true;
            current_arg++;
            continue;
        }
        
        if (arg == "--screenshot") {
            config.take_screenshot = true;
            current_arg++;
            if (current_arg < argc && argv[current_arg][0] != '-') {
                config.screenshot_path = argv[current_arg];
                current_arg++;
            } else {
                config.screenshot_path = "screenshot.png";
            }
            continue;
        }
        
        if (arg == "--exec") {
            current_arg++;
            if (current_arg >= argc) {
                std::cerr << "Argument expected for the --exec option" << std::endl;
                result.should_exit = true;
                result.exit_code = 1;
                return result;
            }
            config.exec_scripts.push_back(argv[current_arg]);
            config.python_mode = true;
            current_arg++;
            // Look for `--` passthrough marker: everything after it becomes script_args
            // (forwarded to sys.argv so fuzzers/libFuzzer can receive their flags).
            int scan = current_arg;
            while (scan < argc) {
                if (std::string(argv[scan]) == "--") {
                    for (int i = scan + 1; i < argc; i++) {
                        config.script_args.push_back(argv[i]);
                    }
                    current_arg = argc;
                    break;
                }
                scan++;
            }
            continue;
        }

        if (arg == "--use-virtual-env") {
            config.use_virtual_env = true;
            current_arg++;
            continue;
        }

        if (arg == "--continue-after-exceptions") {
            config.exit_on_exception = false;
            current_arg++;
            continue;
        }
        
        // If no flags matched, treat as positional argument (script name)
        if (arg[0] != '-') {
            config.script_path = arg;
            config.python_mode = true;
            current_arg++;
            // Remaining args are script args
            while (current_arg < argc) {
                config.script_args.push_back(argv[current_arg]);
                current_arg++;
            }
            break;
        }
        
        // Unknown flag
        std::cerr << "Unknown option: " << arg << std::endl;
        result.should_exit = true;
        result.exit_code = 1;
        return result;
    }

    // #451: -c and -m run Python and exit without running a frame, so they don't open a
    // window or an audio device (as when the binary is invoked as "python"). -i keeps
    // the engine, since an interactive session can go on to drive it.
    if ((!config.python_command.empty() || !config.python_module.empty()) && !config.interactive_mode) {
        config.headless = true;
        if (!config.audio_explicit) config.audio_enabled = false;
    }

    return result;
}

// Parses one argv entry made of CPython interpreter flags. Returns false (with result set)
// on error. Advances current_arg past the entry and any separate -W/-X value.
bool CommandLineParser::parse_interpreter_flags(const std::string& arg, McRogueFaceConfig& config,
                                                ParseResult& result) {
    current_arg++;
    for (size_t i = 1; i < arg.size(); i++) {
        char c = arg[i];
        switch (c) {
            case 'I': config.isolated = true; break;
            case 'E': config.ignore_environment = true; break;
            case 's': config.no_user_site = true; break;
            case 'S': config.no_site = true; break;
            case 'B': config.dont_write_bytecode = true; break;
            case 'u': config.unbuffered = true; break;
            case 'q': config.quiet = true; break;
            case 'v': config.verbose++; break;
            case 'O': config.optimize++; break;
            case 'W':
            case 'X': {
                std::string value = arg.substr(i + 1);
                if (value.empty()) {
                    if (current_arg >= argc) {
                        std::cerr << "Argument expected for the -" << c << " option" << std::endl;
                        result.should_exit = true;
                        result.exit_code = 1;
                        return false;
                    }
                    value = argv[current_arg++];
                }
                (c == 'W' ? config.warnoptions : config.xoptions).push_back(value);
                return true;  // the value consumed the rest of this entry
            }
            default:
                std::cerr << "Unknown option: -" << c << std::endl;
                result.should_exit = true;
                result.exit_code = 1;
                return false;
        }
    }
    return true;
}

void CommandLineParser::print_help() {
    std::cout << "usage: mcrogueface [option] ... [-c cmd | -m mod | file | -] [arg] ...\n"
              << "Options:\n"
              << "  -c cmd : program passed in as string (terminates option list; implies --headless)\n"
              << "  -h     : print this help message and exit (also --help)\n"
              << "  -i     : inspect interactively after running script\n"
              << "  -m mod : run library module as a script (terminates option list; implies --headless)\n"
              << "  -I     : isolate from the user's environment and site (implies -E and -s)\n"
              << "  -E     : ignore PYTHON* environment variables (PYTHONPATH, PYTHONHOME, ...)\n"
              << "  -s     : don't add the user site-packages directory to sys.path\n"
              << "  -S     : don't imply 'import site' on initialization\n"
              << "  -B     : don't write .pyc files on import\n"
              << "  -u     : force the stdout and stderr streams to be unbuffered\n"
              << "  -q     : don't print version and copyright messages on interactive startup\n"
              << "  -v     : verbose (trace import statements); can be repeated\n"
              << "  -O     : remove assert statements; -OO also discards docstrings\n"
              << "  -W arg : warning control (action:message:category:module:lineno); repeatable\n"
              << "  -X opt : set an implementation-specific option (e.g. -X dev); repeatable\n"
              << "           (flags may be clustered as in python: -Es; unknown flags are errors)\n"
              << "  -V     : print the Python version number and exit (also --version)\n"
              << "\n"
              << "McRogueFace specific options:\n"
              << "  --exec file  : run this script instead of scripts/game.py (can be used multiple times)\n"
              << "  --headless   : run without creating a window (implies --audio-off)\n"
              << "  --run-forever : keep running after --exec scripts finish, instead of\n"
              << "                       exiting (for a long-lived headless process)\n"
              << "  --audio-off  : disable audio\n"
              << "  --audio-on   : enable audio (even in headless mode)\n"
              << "  --screenshot [path] : take a screenshot in headless mode\n"
              << "  --continue-after-exceptions : don't exit on Python callback exceptions\n"
              << "                       (default: exit on first exception)\n"
              << "  --use-virtual-env : honour VIRTUAL_ENV in a packaged game, which ignores it\n"
              << "                       by default"
              << "\n"
              << "Arguments:\n"
              << "  file   : program read from script file\n"
              << "  -      : program read from stdin\n"
              << "  arg ...: arguments passed to program in sys.argv[1:]\n";
}

void CommandLineParser::print_version() {
#ifdef Py_GIL_DISABLED
    std::cout << "Python " PY_VERSION " free-threading build (McRogueFace embedded)\n";
#else
    std::cout << "Python " PY_VERSION " (McRogueFace embedded)\n";
#endif
}