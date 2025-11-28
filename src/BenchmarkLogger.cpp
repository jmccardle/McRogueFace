#include "BenchmarkLogger.h"
#include "GameEngine.h"

// Global benchmark logger instance
BenchmarkLogger g_benchmarkLogger;

void BenchmarkLogger::recordFrame(const ProfilingMetrics& metrics) {
    if (!running) return;

    auto now = std::chrono::high_resolution_clock::now();
    double timestamp_ms = std::chrono::duration<double, std::milli>(now - start_time).count();

    BenchmarkFrame frame;
    frame.frame_number = ++frame_counter;
    frame.timestamp_ms = timestamp_ms;
    frame.frame_time_ms = metrics.frameTime;
    frame.fps = metrics.fps;

    frame.grid_render_ms = metrics.gridRenderTime;
    frame.entity_render_ms = metrics.entityRenderTime;
    frame.python_time_ms = metrics.pythonScriptTime;
    frame.animation_time_ms = metrics.animationTime;
    frame.fov_overlay_ms = metrics.fovOverlayTime;

    frame.draw_calls = metrics.drawCalls;
    frame.ui_elements = metrics.uiElements;
    frame.visible_elements = metrics.visibleElements;
    frame.grid_cells_rendered = metrics.gridCellsRendered;
    frame.entities_rendered = metrics.entitiesRendered;
    frame.total_entities = metrics.totalEntities;

    // Move pending logs to this frame
    frame.logs = std::move(pending_logs);
    pending_logs.clear();

    frames.push_back(std::move(frame));
}
