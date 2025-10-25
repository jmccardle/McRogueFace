#pragma once

#include <chrono>
#include <string>
#include <vector>
#include <fstream>

/**
 * @brief Simple RAII-based profiling timer for measuring code execution time
 *
 * Usage:
 *   float timing = 0.0f;
 *   {
 *       ScopedTimer timer(timing);
 *       // ... code to profile ...
 *   } // timing now contains elapsed milliseconds
 */
class ScopedTimer {
private:
    std::chrono::high_resolution_clock::time_point start;
    float& target_ms;

public:
    /**
     * @brief Construct a new Scoped Timer and start timing
     * @param target Reference to float that will receive elapsed time in milliseconds
     */
    explicit ScopedTimer(float& target)
        : target_ms(target)
    {
        start = std::chrono::high_resolution_clock::now();
    }

    /**
     * @brief Destructor automatically records elapsed time
     */
    ~ScopedTimer() {
        auto end = std::chrono::high_resolution_clock::now();
        target_ms = std::chrono::duration<float, std::milli>(end - start).count();
    }

    // Prevent copying
    ScopedTimer(const ScopedTimer&) = delete;
    ScopedTimer& operator=(const ScopedTimer&) = delete;
};

/**
 * @brief Accumulating timer that adds elapsed time to existing value
 *
 * Useful for measuring total time across multiple calls in a single frame
 */
class AccumulatingTimer {
private:
    std::chrono::high_resolution_clock::time_point start;
    float& target_ms;

public:
    explicit AccumulatingTimer(float& target)
        : target_ms(target)
    {
        start = std::chrono::high_resolution_clock::now();
    }

    ~AccumulatingTimer() {
        auto end = std::chrono::high_resolution_clock::now();
        target_ms += std::chrono::duration<float, std::milli>(end - start).count();
    }

    AccumulatingTimer(const AccumulatingTimer&) = delete;
    AccumulatingTimer& operator=(const AccumulatingTimer&) = delete;
};

/**
 * @brief CSV profiling data logger for batch analysis
 *
 * Writes profiling data to CSV file for later analysis with Python/pandas/Excel
 */
class ProfilingLogger {
private:
    std::ofstream file;
    bool headers_written;
    std::vector<std::string> column_names;

public:
    ProfilingLogger();
    ~ProfilingLogger();

    /**
     * @brief Open a CSV file for writing profiling data
     * @param filename Path to CSV file
     * @param columns Column names for the CSV header
     * @return true if file opened successfully
     */
    bool open(const std::string& filename, const std::vector<std::string>& columns);

    /**
     * @brief Write a row of profiling data
     * @param values Data values (must match column count)
     */
    void writeRow(const std::vector<float>& values);

    /**
     * @brief Close the file and flush data
     */
    void close();

    /**
     * @brief Check if logger is ready to write
     */
    bool isOpen() const { return file.is_open(); }
};
