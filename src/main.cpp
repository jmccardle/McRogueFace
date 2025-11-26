#include <SFML/Graphics.hpp>
#include "GameEngine.h"
#include "CommandLineParser.h"
#include "McRogueFaceConfig.h"
#include "McRFPy_API.h"
#include "PyFont.h"
#include "PyTexture.h"
#include <Python.h>
#include <iostream>
#include <filesystem>

// Forward declarations
int run_game_engine(const McRogueFaceConfig& config);
int run_python_interpreter(const McRogueFaceConfig& config);

int main(int argc, char* argv[])
{
    McRogueFaceConfig config;
    CommandLineParser parser(argc, argv);

    // Parse arguments
    auto parse_result = parser.parse(config);
    if (parse_result.should_exit) {
        return parse_result.exit_code;
    }

    // Special handling for -m module: let Python handle modules properly
    if (!config.python_module.empty()) {
        config.python_mode = true;
    }

    // Initialize based on configuration
    if (config.python_mode) {
        return run_python_interpreter(config);
    } else {
        return run_game_engine(config);
    }
}

int run_game_engine(const McRogueFaceConfig& config)
{
    GameEngine g(config);
    g.run();
    if (Py_IsInitialized()) {
        McRFPy_API::api_shutdown();
    }

    // Return exception exit code if a Python exception signaled exit
    if (McRFPy_API::shouldExit()) {
        return McRFPy_API::exit_code.load();
    }
    return 0;
}

int run_python_interpreter(const McRogueFaceConfig& config)
{
    // Create a game engine with the requested configuration
    GameEngine* engine = new GameEngine(config);

    // Initialize Python with configuration (argv is constructed from config)
    McRFPy_API::init_python_with_config(config);
    
    // Import mcrfpy module and store reference
    McRFPy_API::mcrf_module = PyImport_ImportModule("mcrfpy");
    if (!McRFPy_API::mcrf_module) {
        PyErr_Print();
        std::cerr << "Failed to import mcrfpy module" << std::endl;
    } else {
        // Set up default_font and default_texture if not already done
        if (!McRFPy_API::default_font) {
            McRFPy_API::default_font = std::make_shared<PyFont>("assets/JetbrainsMono.ttf");
            McRFPy_API::default_texture = std::make_shared<PyTexture>("assets/kenney_tinydungeon.png", 16, 16);
        }
        PyObject_SetAttrString(McRFPy_API::mcrf_module, "default_font", McRFPy_API::default_font->pyObject());
        PyObject_SetAttrString(McRFPy_API::mcrf_module, "default_texture", McRFPy_API::default_texture->pyObject());
    }
    
    // Handle different Python modes
    if (!config.python_command.empty()) {
        // Execute command from -c
        if (config.interactive_mode) {
            // Use PyRun_String to catch SystemExit
            PyObject* main_module = PyImport_AddModule("__main__");
            PyObject* main_dict = PyModule_GetDict(main_module);
            PyObject* result_obj = PyRun_String(config.python_command.c_str(), 
                                              Py_file_input, main_dict, main_dict);
            
            if (result_obj == NULL) {
                // Check if it's SystemExit
                if (PyErr_Occurred()) {
                    PyObject *type, *value, *traceback;
                    PyErr_Fetch(&type, &value, &traceback);
                    
                    // If it's SystemExit and we're in interactive mode, clear it
                    if (PyErr_GivenExceptionMatches(type, PyExc_SystemExit)) {
                        PyErr_Clear();
                    } else {
                        // Re-raise other exceptions
                        PyErr_Restore(type, value, traceback);
                        PyErr_Print();
                    }
                    
                    Py_XDECREF(type);
                    Py_XDECREF(value);
                    Py_XDECREF(traceback);
                }
            } else {
                Py_DECREF(result_obj);
            }
            // Continue to interactive mode below
        } else {
            int result = PyRun_SimpleString(config.python_command.c_str());
            McRFPy_API::api_shutdown();
            delete engine;
            return result;
        }
    }
    else if (!config.python_module.empty()) {
        // Execute module using runpy (sys.argv already set at init time)
        std::string run_module_code =
            "import runpy\n"
            "runpy.run_module('" + config.python_module + "', run_name='__main__', alter_sys=True)\n";

        int result = PyRun_SimpleString(run_module_code.c_str());
        McRFPy_API::api_shutdown();
        delete engine;
        return result;
    }
    else if (!config.script_path.empty()) {
        // Execute script file (sys.argv already set at init time)
        FILE* fp = fopen(config.script_path.string().c_str(), "r");
        if (!fp) {
            std::cerr << "mcrogueface: can't open file '" << config.script_path << "': ";
            std::cerr << "[Errno " << errno << "] " << strerror(errno) << std::endl;
            return 1;
        }

        int result = PyRun_SimpleFile(fp, config.script_path.string().c_str());
        fclose(fp);
        
        if (config.interactive_mode) {
            // Even if script had SystemExit, continue to interactive mode
            if (result != 0) {
                // Check if it was SystemExit
                if (PyErr_Occurred()) {
                    PyObject *type, *value, *traceback;
                    PyErr_Fetch(&type, &value, &traceback);
                    
                    if (PyErr_GivenExceptionMatches(type, PyExc_SystemExit)) {
                        PyErr_Clear();
                        result = 0; // Don't exit with error
                    } else {
                        PyErr_Restore(type, value, traceback);
                        PyErr_Print();
                    }
                    
                    Py_XDECREF(type);
                    Py_XDECREF(value);
                    Py_XDECREF(traceback);
                }
            }
            // Run interactive mode after script
            PyRun_InteractiveLoop(stdin, "<stdin>");
        }
        
        // Run the game engine after script execution
        engine->run();

        McRFPy_API::api_shutdown();
        delete engine;
        // Return exception exit code if signaled
        if (McRFPy_API::shouldExit()) {
            return McRFPy_API::exit_code.load();
        }
        return result;
    }
    else if (config.interactive_mode) {
        // Interactive Python interpreter (only if explicitly requested with -i)
        // Note: pyconfig.inspect is set at init time based on config.interactive_mode
        PyRun_InteractiveLoop(stdin, "<stdin>");
        McRFPy_API::api_shutdown();
        delete engine;
        return 0;
    }
    else if (!config.exec_scripts.empty()) {
        // Execute startup scripts on the existing engine (not in constructor to prevent double-execution)
        engine->executeStartupScripts();
        if (config.headless) {
            engine->setAutoExitAfterExec(true);
        }
        engine->run();
        McRFPy_API::api_shutdown();
        delete engine;
        // Return exception exit code if signaled
        if (McRFPy_API::shouldExit()) {
            return McRFPy_API::exit_code.load();
        }
        return 0;
    }
    
    delete engine;
    return 0;
}
