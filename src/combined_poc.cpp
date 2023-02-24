// Python script engine includes
#include <Python.h>
#include <iostream>
#include <stdlib.h>
#include <vector>

// wstring<->string conversion
#include <locale>
#include <codecvt>

// SFML
#include <SFML/Graphics.hpp>
#include <SFML/Audio.hpp>

sf::RenderWindow window;
sf::Font font;
sf::Text text;

// TCOD
#include <libtcod.hpp>

#include "platform.h"


std::string narrow_string(std::wstring convertme)
{
    //setup converter
    using convert_type = std::codecvt_utf8<wchar_t>;
    std::wstring_convert<convert_type, wchar_t> converter;

    //use converter (.to_bytes: wstr->str, .from_bytes: str->wstr)
    return converter.to_bytes(convertme);
}

bool fexists(std::string filename)
{
    return std::filesystem::exists(filename);
}

// init_python - configure interpreter details here
PyStatus init_python(const char *program_name)
{
    std::cout << "called init_python" << std::endl;
    PyStatus status;

	//**preconfig to establish locale**
    PyPreConfig preconfig;
    PyPreConfig_InitIsolatedConfig(&preconfig);
    
    preconfig.utf8_mode = 1;
    
    status = Py_PreInitialize(&preconfig);
    if (PyStatus_Exception(status)) {
    	Py_ExitStatusException(status);
    }

    PyConfig config;
    PyConfig_InitIsolatedConfig(&config);
	config.dev_mode = 1;


	PyConfig_SetBytesString(&config, &config.home, 
        narrow_string(executable_path() + L"/Python311").c_str());
    std::cout << "config.home: "; std::wcout << config.home << std::endl;

    /* Set the program name before reading the configuration
       (decode byte string from the locale encoding).

       Implicitly preinitialize Python. */

    // windows can't name the Python interpreter...?
    status = PyConfig_SetBytesString(&config, &config.program_name,
                                     program_name);

    // under Windows, the search paths are correct; under Linux, they need manual insertion
#if __PLATFORM_SET_PYTHON_SEARCH_PATHS == 1
    config.module_search_paths_set = 1;
	
	// search paths for python libs/modules/scripts
    const wchar_t* str_arr[] = {
        L"/scripts",
        L"/Python311/lib.linux-x86_64-3.11",
	    L"/Python311",
        L"/Python311/Lib",
        L"/venv/lib/python3.11/site-packages"
    };
    

    for(auto s : str_arr) {
        status = PyWideStringList_Append(&config.module_search_paths, (executable_path() + s).c_str());
		std::wcout << "`" << s 
            << "` transformed to `" << (executable_path() + s).c_str() 
            << "` and got status error (`" << PyStatus_IsError(status) << "`)" << std::endl;

        if (PyStatus_Exception(status)) {
			std::wcout << "Exception handling " << s << std::endl << std::flush;
            break;
        }
    }
#endif

    status = Py_InitializeFromConfig(&config);
	std::cout << "Python Initialized" << std::endl;

done:
    //PyConfig_Clear(&config);
    //free(python_home_ptr);
    return status;
}


// C++ example functionality
int recurse_fib(int i)
{
    if (i <= 1) return 1;
    return recurse_fib(i-1) + recurse_fib(i-2);
}

// Create a python module to expose C++ functionality
static PyObject* scriptable_fibonacci(PyObject *self, PyObject *args)
{
    int x;
    // get input (single integer) from args
    if (!PyArg_ParseTuple(args, "i", &x)) return NULL;
    return PyLong_FromLong(recurse_fib(x));
}

static PyMethodDef scriptableMethods[] = {
    {"fibonacci", scriptable_fibonacci, METH_VARARGS,
        "Fibonacci sequence by index"},
    {NULL, NULL, 0, NULL}
};

static PyModuleDef scriptableModule = {
    PyModuleDef_HEAD_INIT, "scriptable", NULL, -1, scriptableMethods,
    NULL, NULL, NULL, NULL
};

static PyObject* PyInit_scriptable(void)
{
    return PyModule_Create(&scriptableModule);
}

int main(int argc, char ** argv)
{
    std::cout << "Output." << std::endl;
    std::wcout << "Current executable path: " << executable_path()
        << "\nCurrent working directory: " << working_path() << std::endl;

    std::cout << "[C++] Initializing Python\n";
    //setenv("PYTHONHOME", "./Python-3.11.1", 0);
    //Express this program as a module before pyinit
    PyImport_AppendInittab("scriptable", &PyInit_scriptable);
	//Initialize the python instance
    
    //Py_SetPythonHome is deprecated
    //Py_SetPythonHome(L"./lib/python-dist");
    
    std::cout << "Output. (2)" << std::endl;
    PyStatus status = init_python(argv[0]);
    std::cout << "Output. (3)" << std::endl;

    std::cout << "***\n[C++] Executing some Python\n***\n";
    int result = PyRun_SimpleString("import sys,datetime\n"
        "print('test\\n', datetime.__file__)\n");
    std::cout << "\n***\n[C++] Execution Complete\nResult = " << result << std::endl;

	std::cout << "On to other modules..." << std::endl;

    //Py_Initialize();


    std::string asset_path = narrow_string(executable_path()) + "/assets";
    std::string script_path = narrow_string(executable_path()) + "/scripts";

    // SFML demo setup
    //font.loadFromFile("./assets/JetbrainsMono.ttf");
    font.loadFromFile(asset_path + "/JetbrainsMono.ttf");
    window.create(sf::VideoMode(640, 480), "Python/SFML/TCOD test");


    // TCOD demo setup

	//Run a simple string
	PyRun_SimpleString("from time import time,ctime\n"
						"print('Today is',ctime(time()))\n");

    std::cout << "[C++] Executing engine_user.py\n";
    //FILE* PScriptFile = fopen("./scripts/engine_user.py", "r");
    FILE* PScriptFile = fopen((script_path + "/engine_user.py").c_str(), "r");
    if(PScriptFile) {
        PyRun_SimpleFile(PScriptFile, "engine_user.py");
        fclose(PScriptFile);
    }
    /*
    std::cout << "[C++] Executing Python string\n";
    PyRun_SimpleString("import sys;print(sys.version)");

	//Run a simple file
    std::cout << "[C++] executing the contents of test.py\n";
	FILE* PScriptFile = fopen("test.py", "r");
	if(PScriptFile){
		PyRun_SimpleFile(PScriptFile, "test.py");
		fclose(PScriptFile);
	}

    std::cout << "[C++] importing script.script_function and executing from C++. Aquiring GIL...\n";
	//Run a python function
	PyObject *pName, *pModule, *pFunc, *pArgs, *pValue;

	pName = PyUnicode_FromString((char*)"script");

    // acquire GIL
    PyGILState_STATE gstate;
    gstate = PyGILState_Ensure();

	pModule = PyImport_Import(pName);
	pFunc = PyObject_GetAttrString(pModule, (char*)"script_function");
	pArgs = PyTuple_Pack(1, PyUnicode_FromString((char*)"Embedded Python"));
	pValue = PyObject_CallObject(pFunc, pArgs);
	
    std::cout << "[C++] Result:\n";
	auto result = _PyUnicode_AsString(pValue);
	std::cout << result << std::endl;

    // release GIL
    PyGILState_Release(gstate);
    */

    // TCOD functionality - gather noise
    TCODNoise noise_{2, TCOD_NOISE_SIMPLEX};
    float hurst_ = TCOD_NOISE_DEFAULT_HURST;
    float lacunarity_ = TCOD_NOISE_DEFAULT_LACUNARITY;
    noise_ = TCODNoise(2, hurst_, lacunarity_);

    float display_noise[64][48];
    int generated = 0;
    float n_min = 0, n_max = 0;
    for (int x = 0; x < 64; x++) {
        for (int y = 0; y < 48; y++) {
            float f[2] = {float(x * 10 + 5) / 100.0f, float(y * 10 + 5) / 100.0f};
            display_noise[x][y] = float(noise_.get(f, TCOD_NOISE_SIMPLEX));
            //display_noise[x][y] = float(rand()) / RAND_MAX;
            generated++;
            if (display_noise[x][y] > n_max) n_max = display_noise[x][y];
            else if (display_noise[x][y] < n_min) n_min = display_noise[x][y];
        }
    }

    std::cout << "Generated " << generated << " points of noise: " 
        << n_min << " - " << n_max << std::endl;

    // SFML/graphical run
    window.setFramerateLimit(30);
    text.setFont(font);
    text.setString("asdf");
    text.setCharacterSize(16);

    bool running = true;
    while (running) {
        // render
        window.clear();
        // draw boxes of noise
        for (int x = 0; x < 64; x++) {
            for (int y = 0; y < 48; y++) {
                //int x1 = x * 10, x2 = (x+1) * 10, y1 = y * 10, y2 = (y+1) * 10;
                sf::RectangleShape r;
                r.setPosition(sf::Vector2f(x * 10, y * 10));
                r.setSize(sf::Vector2f(10, 10));
                r.setOutlineThickness(0);
                r.setFillColor(sf::Color(display_noise[x][y] * 255, 0, 0));
                window.draw(r);
            }
        }
        window.draw(text);
        window.display();

        // user input
        sf::Event event;
        while (window.pollEvent(event)) {
            if (event.type == sf::Event::Closed) { running = false; continue; }
        }

    }

	//Close the python instance
	Py_Finalize();

    std::cout << "[C++] Exiting normally.\n";
    return 0;
}

