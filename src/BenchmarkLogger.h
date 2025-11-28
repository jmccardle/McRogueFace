#pragma once

#include <string>
#include <vector>
#include <chrono>
#include <fstream>
#include <sstream>
#include <iomanip>
#include <stdexcept>

#ifdef _WIN32
#include <process.h>
#define getpid _getpid
#else
#include <unistd.h>
#endif

// Forward declaration
struct ProfilingMetrics;

/**
 * @brief Frame data captured during benchmarking
 */
struct BenchmarkFrame {
    int frame_number;
    double timestamp_ms;        // Time since benchmark start
    float frame_time_ms;
    int fps;

    // Detailed timing breakdown
    float work_time_ms;       // Actual work time (frame_time - sleep_time)
    float grid_render_ms;
    float entity_render_ms;
    float python_time_ms;
    float animation_time_ms;
    float fov_overlay_ms;

    // Counts
    int draw_calls;
    int ui_elements;
    int visible_elements;
    int grid_cells_rendered;
    int entities_rendered;
    int total_entities;

    // User-provided log messages for this frame
    std::vector<std::string> logs;
};

/**
 * @brief Benchmark logging system for capturing performance data to JSON files
 *
 * Usage from Python:
 *   mcrfpy.start_benchmark()      # Start capturing
 *   mcrfpy.log_benchmark("msg")   # Add comment to current frame
 *   filename = mcrfpy.end_benchmark()  # Stop and get filename
 */
class BenchmarkLogger {
private:
    bool running;
    std::string filename;
    std::chrono::high_resolution_clock::time_point start_time;
    std::vector<BenchmarkFrame> frames;
    std::vector<std::string> pending_logs;  // Logs for current frame (before it's recorded)
    int frame_counter;

    // Generate filename based on PID and timestamp
    std::string generateFilename() {
        auto now = std::chrono::system_clock::now();
        auto time_t = std::chrono::system_clock::to_time_t(now);
        std::tm tm = *std::localtime(&time_t);

        std::ostringstream oss;
        oss << "benchmark_" << getpid() << "_"
            << std::put_time(&tm, "%Y%m%d_%H%M%S") << ".json";
        return oss.str();
    }

    // Get current timestamp as ISO 8601 string
    std::string getCurrentTimestamp() {
        auto now = std::chrono::system_clock::now();
        auto time_t = std::chrono::system_clock::to_time_t(now);
        std::tm tm = *std::localtime(&time_t);

        std::ostringstream oss;
        oss << std::put_time(&tm, "%Y-%m-%dT%H:%M:%S");
        return oss.str();
    }

    // Escape string for JSON
    std::string escapeJson(const std::string& str) {
        std::ostringstream oss;
        for (char c : str) {
            switch (c) {
                case '"':  oss << "\\\""; break;
                case '\\': oss << "\\\\"; break;
                case '\b': oss << "\\b"; break;
                case '\f': oss << "\\f"; break;
                case '\n': oss << "\\n"; break;
                case '\r': oss << "\\r"; break;
                case '\t': oss << "\\t"; break;
                default:
                    if ('\x00' <= c && c <= '\x1f') {
                        oss << "\\u" << std::hex << std::setw(4) << std::setfill('0') << (int)c;
                    } else {
                        oss << c;
                    }
            }
        }
        return oss.str();
    }

    std::string start_timestamp;

public:
    BenchmarkLogger() : running(false), frame_counter(0) {}

    /**
     * @brief Start benchmark logging
     * @throws std::runtime_error if already running
     */
    void start() {
        if (running) {
            throw std::runtime_error("Benchmark already running. Call end_benchmark() first.");
        }

        running = true;
        filename = generateFilename();
        start_time = std::chrono::high_resolution_clock::now();
        start_timestamp = getCurrentTimestamp();
        frames.clear();
        pending_logs.clear();
        frame_counter = 0;
    }

    /**
     * @brief Stop benchmark logging and write to file
     * @return The filename that was written
     * @throws std::runtime_error if not running
     */
    std::string end() {
        if (!running) {
            throw std::runtime_error("No benchmark running. Call start_benchmark() first.");
        }

        running = false;

        // Calculate duration
        auto end_time = std::chrono::high_resolution_clock::now();
        double duration_seconds = std::chrono::duration<double>(end_time - start_time).count();
        std::string end_timestamp = getCurrentTimestamp();

        // Write JSON file
        std::ofstream file(filename);
        if (!file.is_open()) {
            throw std::runtime_error("Failed to open benchmark file for writing: " + filename);
        }

        file << "{\n";
        file << "  \"benchmark\": {\n";
        file << "    \"pid\": " << getpid() << ",\n";
        file << "    \"start_time\": \"" << start_timestamp << "\",\n";
        file << "    \"end_time\": \"" << end_timestamp << "\",\n";
        file << "    \"total_frames\": " << frames.size() << ",\n";
        file << "    \"duration_seconds\": " << std::fixed << std::setprecision(3) << duration_seconds << "\n";
        file << "  },\n";

        file << "  \"frames\": [\n";
        for (size_t i = 0; i < frames.size(); ++i) {
            const auto& f = frames[i];
            file << "    {\n";
            file << "      \"frame_number\": " << f.frame_number << ",\n";
            file << "      \"timestamp_ms\": " << std::fixed << std::setprecision(3) << f.timestamp_ms << ",\n";
            file << "      \"frame_time_ms\": " << std::setprecision(3) << f.frame_time_ms << ",\n";
            file << "      \"fps\": " << f.fps << ",\n";
            file << "      \"work_time_ms\": " << std::setprecision(3) << f.work_time_ms << ",\n";
            file << "      \"grid_render_ms\": " << std::setprecision(3) << f.grid_render_ms << ",\n";
            file << "      \"entity_render_ms\": " << std::setprecision(3) << f.entity_render_ms << ",\n";
            file << "      \"python_time_ms\": " << std::setprecision(3) << f.python_time_ms << ",\n";
            file << "      \"animation_time_ms\": " << std::setprecision(3) << f.animation_time_ms << ",\n";
            file << "      \"fov_overlay_ms\": " << std::setprecision(3) << f.fov_overlay_ms << ",\n";
            file << "      \"draw_calls\": " << f.draw_calls << ",\n";
            file << "      \"ui_elements\": " << f.ui_elements << ",\n";
            file << "      \"visible_elements\": " << f.visible_elements << ",\n";
            file << "      \"grid_cells_rendered\": " << f.grid_cells_rendered << ",\n";
            file << "      \"entities_rendered\": " << f.entities_rendered << ",\n";
            file << "      \"total_entities\": " << f.total_entities << ",\n";

            // Write logs array
            file << "      \"logs\": [";
            for (size_t j = 0; j < f.logs.size(); ++j) {
                file << "\"" << escapeJson(f.logs[j]) << "\"";
                if (j < f.logs.size() - 1) file << ", ";
            }
            file << "]\n";

            file << "    }";
            if (i < frames.size() - 1) file << ",";
            file << "\n";
        }
        file << "  ]\n";
        file << "}\n";

        file.close();

        std::string result = filename;
        filename.clear();
        frames.clear();
        pending_logs.clear();
        frame_counter = 0;

        return result;
    }

    /**
     * @brief Add a log message to the current frame
     * @param message The message to log
     * @throws std::runtime_error if not running
     */
    void log(const std::string& message) {
        if (!running) {
            throw std::runtime_error("No benchmark running. Call start_benchmark() first.");
        }
        pending_logs.push_back(message);
    }

    /**
     * @brief Record frame data (called by game loop at end of each frame)
     * @param metrics The current frame's profiling metrics
     */
    void recordFrame(const ProfilingMetrics& metrics);

    /**
     * @brief Check if benchmark is currently running
     */
    bool isRunning() const { return running; }

    /**
     * @brief Get current frame count
     */
    int getFrameCount() const { return frame_counter; }
};

// Global benchmark logger instance
extern BenchmarkLogger g_benchmarkLogger;
