#ifndef __PLATFORM
#define __PLATFORM
#define __PLATFORM_SET_PYTHON_SEARCH_PATHS 1
#include <windows.h>

std::wstring executable_path()
{
	wchar_t buffer[MAX_PATH];
	GetModuleFileNameW(NULL, buffer, MAX_PATH);  // Use explicit Unicode version
	std::wstring exec_path = buffer;
	size_t path_index = exec_path.find_last_of(L"\\/");
	return exec_path.substr(0, path_index);
}

std::wstring executable_filename()
{
	wchar_t buffer[MAX_PATH];
	GetModuleFileNameW(NULL, buffer, MAX_PATH);  // Use explicit Unicode version
	std::wstring exec_path = buffer;
	return exec_path;
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
