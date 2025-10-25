#include "Profiler.h"
#include <iostream>

ProfilingLogger::ProfilingLogger()
    : headers_written(false)
{
}

ProfilingLogger::~ProfilingLogger() {
    close();
}

bool ProfilingLogger::open(const std::string& filename, const std::vector<std::string>& columns) {
    column_names = columns;
    file.open(filename);

    if (!file.is_open()) {
        std::cerr << "Failed to open profiling log file: " << filename << std::endl;
        return false;
    }

    // Write CSV header
    for (size_t i = 0; i < columns.size(); ++i) {
        file << columns[i];
        if (i < columns.size() - 1) {
            file << ",";
        }
    }
    file << "\n";
    file.flush();

    headers_written = true;
    return true;
}

void ProfilingLogger::writeRow(const std::vector<float>& values) {
    if (!file.is_open()) {
        return;
    }

    if (values.size() != column_names.size()) {
        std::cerr << "ProfilingLogger: value count (" << values.size()
                  << ") doesn't match column count (" << column_names.size() << ")" << std::endl;
        return;
    }

    for (size_t i = 0; i < values.size(); ++i) {
        file << values[i];
        if (i < values.size() - 1) {
            file << ",";
        }
    }
    file << "\n";
}

void ProfilingLogger::close() {
    if (file.is_open()) {
        file.flush();
        file.close();
    }
}
