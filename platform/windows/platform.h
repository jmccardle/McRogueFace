#ifndef __PLATFORM
#define __PLATFORM
#define __PLATFORM_SET_PYTHON_SEARCH_PATHS 0
#include <Windows.h>

std::wstring executable_path()
{
	wchar_t buffer[MAX_PATH];
	GetModuleFileName(NULL, buffer, MAX_PATH);
	std::wstring exec_path = buffer;
	size_t path_index = exec_path.find_last_of(L"\\/");
	return exec_path.substr(0, path_index);
}

std::wstring working_path()
{
	auto cwd = std::filesystem::current_path();
	return cwd.wstring();
}

#endif
