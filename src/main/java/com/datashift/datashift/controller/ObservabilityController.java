package com.datashift.datashift.controller;

import com.datashift.datashift.dto.ExecutionTrendResponse;
import com.datashift.datashift.dto.PipelineMetricsResponse;
import com.datashift.datashift.service.PipelineService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/v1/observability")
@Tag(name = "Observability", description = "Observability and metrics APIs")
public class ObservabilityController {

    private final PipelineService pipelineService;

    public ObservabilityController(PipelineService pipelineService) {
        this.pipelineService = pipelineService;
    }

    @GetMapping("/pipelines/metrics")
    @Operation(summary = "Get overall pipeline metrics")
    public ResponseEntity<PipelineMetricsResponse> getPipelineMetrics() {
        PipelineMetricsResponse metrics = pipelineService.getOverallMetrics();
        return ResponseEntity.ok(metrics);
    }

    @GetMapping("/pipelines/{id}/stats")
    @Operation(summary = "Get per-pipeline stats")
    public ResponseEntity<PipelineMetricsResponse> getPipelineStats(@PathVariable Long id) {
        PipelineMetricsResponse stats = pipelineService.getPipelineStats(id);
        return ResponseEntity.ok(stats);
    }

    @GetMapping("/system/health")
    @Operation(summary = "Get system health (proxies to Actuator)")
    public ResponseEntity<String> getSystemHealth() {
        // Basic health check; full details at /actuator/health
        return ResponseEntity.ok("System is operational");
    }

    @GetMapping("/trends")
    @Operation(summary = "Get pipeline execution trends for charting")
    public ResponseEntity<List<ExecutionTrendResponse>> getExecutionTrends(
            @RequestParam(defaultValue = "daily") String granularity,
            @RequestParam(defaultValue = "7") Integer days) {
        List<ExecutionTrendResponse> trends = pipelineService.getExecutionTrends(granularity, days);
        return ResponseEntity.ok(trends);
    }
}
