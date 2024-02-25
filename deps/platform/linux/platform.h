#ifndef __PLATFORM
#define __PLATFORM
#define __PLATFORM_SET_PYTHON_SEARCH_PATHS 1
std::wstring executable_path()
{
    /*
	wchar_t buffer[MAX_PATH];
	GetModuleFileName(NULL, buffer, MAX_PATH);
	std::wstring exec_path = buffer;
    */
    auto exec_path = std::filesystem::canonical("/proc/self/exe").parent_path();
	return exec_path.wstring();
    //size_t path_index = exec_path.find_last_of('/');
	//return exec_path.substr(0, path_index);
    
}

std::wstring executable_filename()
{
    auto exec_path = std::filesystem::canonical("/proc/self/exe");
    return exec_path.wstring();
}

std::wstring working_path()
{
	auto cwd = std::filesystem::current_path();
	return cwd.wstring();
}

std::string narrow_string(std::wstring convertme)
{
    //setup converter
    using convert_type = std::codecvt_utf8<wchar_t>;
    std::wstring_convert<convert_type, wchar_t> converter;

    //use converter (.to_bytes: wstr->str, .from_bytes: str->wstr)
    return converter.to_bytes(convertme);
}

#endif
