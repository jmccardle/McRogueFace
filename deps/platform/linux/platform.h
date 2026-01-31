#ifndef __PLATFORM
#define __PLATFORM
#define __PLATFORM_SET_PYTHON_SEARCH_PATHS 1

#ifdef __EMSCRIPTEN__
// WASM/Emscripten platform - no /proc filesystem, limited std::filesystem support

std::wstring executable_path()
{
    // In WASM, the executable is at the root of the virtual filesystem
    return L"/";
}

std::wstring executable_filename()
{
    // In WASM, we use a fixed executable name
    return L"/mcrogueface";
}

std::wstring working_path()
{
    // In WASM, working directory is root of virtual filesystem
    return L"/";
}

std::string narrow_string(std::wstring convertme)
{
    // Simple conversion for ASCII/UTF-8 compatible strings
    std::string result;
    result.reserve(convertme.size());
    for (wchar_t wc : convertme) {
        if (wc < 128) {
            result.push_back(static_cast<char>(wc));
        } else {
            // For non-ASCII, use a simple UTF-8 encoding
            if (wc < 0x800) {
                result.push_back(static_cast<char>(0xC0 | (wc >> 6)));
                result.push_back(static_cast<char>(0x80 | (wc & 0x3F)));
            } else {
                result.push_back(static_cast<char>(0xE0 | (wc >> 12)));
                result.push_back(static_cast<char>(0x80 | ((wc >> 6) & 0x3F)));
                result.push_back(static_cast<char>(0x80 | (wc & 0x3F)));
            }
        }
    }
    return result;
}

#else
// Native Linux platform

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

#endif // __EMSCRIPTEN__

#endif // __PLATFORM
