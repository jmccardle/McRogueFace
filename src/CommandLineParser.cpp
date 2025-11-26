#include "CommandLineParser.h"
#include <iostream>
#include <filesystem>
#include <algorithm>

CommandLineParser::CommandLineParser(int argc, char* argv[]) 
    : argc(argc), argv(argv) {}

CommandLineParser::ParseResult CommandLineParser::parse(McRogueFaceConfig& config) {
    ParseResult result;
    current_arg = 1;  // Reset for each parse
    
    // Detect if running as Python interpreter
    std::filesystem::path exec_name = std::filesystem::path(argv[0]).filename();
    if (exec_name.string().find("python") == 0) {
        config.headless = true;
        config.python_mode = true;
    }
    
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
        
        // McRogueFace specific flags
        if (arg == "--headless") {
            config.headless = true;
            config.audio_enabled = false;
            current_arg++;
            continue;
        }
        
        if (arg == "--audio-off") {
            config.audio_enabled = false;
            current_arg++;
            continue;
        }
        
        if (arg == "--audio-on") {
            config.audio_enabled = true;
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
    
    return result;
}

void CommandLineParser::print_help() {
    std::cout << "usage: mcrogueface [option] ... [-c cmd | -m mod | file | -] [arg] ...\n"
              << "Options:\n"
              << "  -c cmd : program passed in as string (terminates option list)\n"
              << "  -h     : print this help message and exit (also --help)\n"
              << "  -i     : inspect interactively after running script\n"
              << "  -m mod : run library module as a script (terminates option list)\n"
              << "  -V     : print the Python version number and exit (also --version)\n"
              << "\n"
              << "McRogueFace specific options:\n"
              << "  --exec file  : execute script before main program (can be used multiple times)\n"
              << "  --headless   : run without creating a window (implies --audio-off)\n"
              << "  --audio-off  : disable audio\n"
              << "  --audio-on   : enable audio (even in headless mode)\n"
              << "  --screenshot [path] : take a screenshot in headless mode\n"
              << "  --continue-after-exceptions : don't exit on Python callback exceptions\n"
              << "                       (default: exit on first exception)\n"
              << "\n"
              << "Arguments:\n"
              << "  file   : program read from script file\n"
              << "  -      : program read from stdin\n"
              << "  arg ...: arguments passed to program in sys.argv[1:]\n";
}

void CommandLineParser::print_version() {
    std::cout << "Python 3.12.0 (McRogueFace embedded)\n";
}