package com.datashift.datashift.controller;

import com.datashift.datashift.dto.PipelineLogResponse;
import com.datashift.datashift.dto.PipelineRequest;
import com.datashift.datashift.dto.PipelineResponse;
import com.datashift.datashift.dto.PipelineRunResponse;
import com.datashift.datashift.service.PipelineService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/v1/pipelines")
@Tag(name = "Pipelines", description = "Pipeline management APIs")
public class PipelineController {

    private final PipelineService pipelineService;

    public PipelineController(PipelineService pipelineService) {
        this.pipelineService = pipelineService;
    }

    @PostMapping
    @Operation(summary = "Create a new pipeline")
    public ResponseEntity<PipelineResponse> createPipeline(@Valid @RequestBody PipelineRequest request) {
        PipelineResponse response = pipelineService.createPipeline(request);
        return new ResponseEntity<>(response, HttpStatus.CREATED);
    }

    @GetMapping
    @Operation(summary = "List all pipelines")
    public ResponseEntity<List<PipelineResponse>> getAllPipelines() {
        List<PipelineResponse> responses = pipelineService.getAllPipelines();
        return ResponseEntity.ok(responses);
    }

    @GetMapping("/{id}")
    @Operation(summary = "Get pipeline by ID")
    public ResponseEntity<PipelineResponse> getPipelineById(@PathVariable Long id) {
        PipelineResponse response = pipelineService.getPipelineById(id);
        return ResponseEntity.ok(response);
    }

    @DeleteMapping("/{id}")
    @Operation(summary = "Delete a pipeline")
    public ResponseEntity<Void> deletePipeline(@PathVariable Long id) {
        pipelineService.deletePipeline(id);
        return ResponseEntity.noContent().build();
    }

    @PostMapping("/{id}/run")
    @Operation(summary = "Execute the pipeline (async)")
    public ResponseEntity<Long> runPipeline(@PathVariable Long id) {
        Long runId = pipelineService.runPipeline(id);
        return ResponseEntity.ok(runId);
    }

    @GetMapping("/{id}/runs")
    @Operation(summary = "List pipeline run history with pagination")
    public ResponseEntity<Page<PipelineRunResponse>> getPipelineRuns(
            @PathVariable Long id,
            Pageable pageable) {
        Page<PipelineRunResponse> runs = pipelineService.getPipelineRuns(id, pageable);
        return ResponseEntity.ok(runs);
    }

    @GetMapping("/{id}/runs/{runId}/logs")
    @Operation(summary = "Get detailed logs for a specific pipeline run")
    public ResponseEntity<List<PipelineLogResponse>> getRunLogs(
            @PathVariable Long id,
            @PathVariable Long runId) {
        List<PipelineLogResponse> logs = pipelineService.getRunLogs(runId);
        return ResponseEntity.ok(logs);
    }
}
