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
int run_python_interpreter(const McRogueFaceConfig& config, int argc, char* argv[]);

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
        return run_python_interpreter(config, argc, argv);
    } else {
        return run_game_engine(config);
    }
}

int run_game_engine(const McRogueFaceConfig& config)
{
    GameEngine g(config);
    g.run();
    return 0;
}

int run_python_interpreter(const McRogueFaceConfig& config, int argc, char* argv[])
{
    // Create a game engine with the requested configuration
    GameEngine* engine = new GameEngine(config);
    
    // Initialize Python with configuration
    McRFPy_API::init_python_with_config(config, argc, argv);
    
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
            Py_Finalize();
            delete engine;
            return result;
        }
    }
    else if (!config.python_module.empty()) {
        // Execute module using runpy
        std::string run_module_code = 
            "import sys\n"
            "import runpy\n"
            "sys.argv = ['" + config.python_module + "'";
        
        for (const auto& arg : config.script_args) {
            run_module_code += ", '" + arg + "'";
        }
        run_module_code += "]\n";
        run_module_code += "runpy.run_module('" + config.python_module + "', run_name='__main__', alter_sys=True)\n";
        
        int result = PyRun_SimpleString(run_module_code.c_str());
        Py_Finalize();
        delete engine;
        return result;
    }
    else if (!config.script_path.empty()) {
        // Execute script file
        FILE* fp = fopen(config.script_path.string().c_str(), "r");
        if (!fp) {
            std::cerr << "mcrogueface: can't open file '" << config.script_path << "': ";
            std::cerr << "[Errno " << errno << "] " << strerror(errno) << std::endl;
            return 1;
        }
        
        // Set up sys.argv
        wchar_t** python_argv = new wchar_t*[config.script_args.size() + 1];
        python_argv[0] = Py_DecodeLocale(config.script_path.string().c_str(), nullptr);
        for (size_t i = 0; i < config.script_args.size(); i++) {
            python_argv[i + 1] = Py_DecodeLocale(config.script_args[i].c_str(), nullptr);
        }
        PySys_SetArgvEx(config.script_args.size() + 1, python_argv, 0);
        
        int result = PyRun_SimpleFile(fp, config.script_path.string().c_str());
        fclose(fp);
        
        // Clean up
        for (size_t i = 0; i <= config.script_args.size(); i++) {
            PyMem_RawFree(python_argv[i]);
        }
        delete[] python_argv;
        
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
        
        Py_Finalize();
        delete engine;
        return result;
    }
    else if (config.interactive_mode) {
        // Interactive Python interpreter (only if explicitly requested with -i)
        Py_InspectFlag = 1;
        PyRun_InteractiveLoop(stdin, "<stdin>");
        Py_Finalize();
        delete engine;
        return 0;
    }
    else if (!config.exec_scripts.empty()) {
        // With --exec, run the game engine after scripts execute
        engine->run();
        Py_Finalize();
        delete engine;
        return 0;
    }
    
    delete engine;
    return 0;
}
