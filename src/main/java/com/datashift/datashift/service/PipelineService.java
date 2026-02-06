package com.datashift.datashift.service;

import com.datashift.datashift.dto.ExecutionTrendResponse;
import com.datashift.datashift.dto.PipelineLogResponse;
import com.datashift.datashift.dto.PipelineMetricsResponse;
import com.datashift.datashift.dto.PipelineRequest;
import com.datashift.datashift.dto.PipelineResponse;
import com.datashift.datashift.dto.PipelineRunResponse;
import com.datashift.datashift.model.Connection;
import com.datashift.datashift.model.Pipeline;
import com.datashift.datashift.model.PipelineLog;
import com.datashift.datashift.model.PipelineRun;
import com.datashift.datashift.repository.ConnectionRepository;
import com.datashift.datashift.repository.PipelineLogRepository;
import com.datashift.datashift.repository.PipelineRepository;
import com.datashift.datashift.repository.PipelineRunRepository;
import com.datashift.datashift.service.AlertService;
import com.datashift.datashift.service.EncryptionService;
import io.micrometer.core.instrument.MeterRegistry;
import io.micrometer.core.instrument.Timer;
import jakarta.persistence.EntityNotFoundException;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.sql.*;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.stream.Collectors;

@Service
@Transactional
public class PipelineService {

    private final PipelineRepository pipelineRepository;
    private final ConnectionRepository connectionRepository;
    private final PipelineRunRepository pipelineRunRepository;
    private final PipelineLogRepository pipelineLogRepository;
    private final EncryptionService encryptionService;
    private final MeterRegistry meterRegistry;
    private final AlertService alertService;

    public PipelineService(PipelineRepository pipelineRepository, ConnectionRepository connectionRepository,
                           PipelineRunRepository pipelineRunRepository, PipelineLogRepository pipelineLogRepository,
                           EncryptionService encryptionService, MeterRegistry meterRegistry,
                           AlertService alertService) {
        this.pipelineRepository = pipelineRepository;
        this.connectionRepository = connectionRepository;
        this.pipelineRunRepository = pipelineRunRepository;
        this.pipelineLogRepository = pipelineLogRepository;
        this.encryptionService = encryptionService;
        this.meterRegistry = meterRegistry;
        this.alertService = alertService;
    }

    public PipelineResponse createPipeline(PipelineRequest request) {
        if (pipelineRepository.findByName(request.getName()).isPresent()) {
            throw new IllegalArgumentException("Pipeline with name '" + request.getName() + "' already exists");
        }

        Connection sourceConn = connectionRepository.findById(request.getSourceConnectionId())
                .orElseThrow(() -> new EntityNotFoundException("Source connection not found with id: " + request.getSourceConnectionId()));

        Connection targetConn = connectionRepository.findById(request.getTargetConnectionId())
                .orElseThrow(() -> new EntityNotFoundException("Target connection not found with id: " + request.getTargetConnectionId()));

        Pipeline pipeline = Pipeline.builder()
                .name(request.getName())
                .sourceConnection(sourceConn)
                .sourceTable(request.getSourceTable())
                .targetConnection(targetConn)
                .targetTable(request.getTargetTable())
                .mappingConfig(request.getMappingConfig())
                .build();

        Pipeline saved = pipelineRepository.save(pipeline);
        return mapToResponse(saved);
    }

    public List<PipelineResponse> getAllPipelines() {
        return pipelineRepository.findAll().stream()
                .map(this::mapToResponse)
                .collect(Collectors.toList());
    }

    public PipelineResponse getPipelineById(Long id) {
        Pipeline pipeline = pipelineRepository.findById(id)
                .orElseThrow(() -> new EntityNotFoundException("Pipeline not found with id: " + id));
        return mapToResponse(pipeline);
    }

    public void deletePipeline(Long id) {
        if (!pipelineRepository.existsById(id)) {
            throw new EntityNotFoundException("Pipeline not found with id: " + id);
        }
        pipelineRepository.deleteById(id);
    }

    public Page<PipelineRunResponse> getPipelineRuns(Long pipelineId, Pageable pageable) {
        // Check pipeline exists
        pipelineRepository.findById(pipelineId)
                .orElseThrow(() -> new EntityNotFoundException("Pipeline not found with id: " + pipelineId));

        return pipelineRunRepository.findByPipelineIdOrderByStartedAtDesc(pipelineId, pageable)
                .map(this::mapToRunResponse);
    }

    public List<PipelineLogResponse> getRunLogs(Long runId) {
        // Check run exists (optional validation)
        pipelineRunRepository.findById(runId)
                .orElseThrow(() -> new EntityNotFoundException("Pipeline run not found with id: " + runId));

        return pipelineLogRepository.findByPipelineRunIdOrderByTimestampAsc(runId).stream()
                .map(this::mapToLogResponse)
                .collect(Collectors.toList());
    }

    private PipelineRunResponse mapToRunResponse(PipelineRun run) {
        return PipelineRunResponse.builder()
                .id(run.getId())
                .pipelineId(run.getPipeline().getId())
                .startedAt(run.getStartedAt())
                .completedAt(run.getCompletedAt())
                .rowsExtracted(run.getRowsExtracted())
                .rowsLoaded(run.getRowsLoaded())
                .status(run.getStatus())
                .errorMessage(run.getErrorMessage())
                .createdAt(run.getCreatedAt())
                .build();
    }

    private PipelineLogResponse mapToLogResponse(PipelineLog log) {
        return PipelineLogResponse.builder()
                .id(log.getId())
                .pipelineRunId(log.getPipelineRun().getId())
                .timestamp(log.getTimestamp())
                .logLevel(log.getLogLevel())
                .message(log.getMessage())
                .build();
    }

    public Long runPipeline(Long id) {
        Pipeline pipeline = pipelineRepository.findById(id)
                .orElseThrow(() -> new EntityNotFoundException("Pipeline not found with id: " + id));

        // Create run record immediately
        PipelineRun run = PipelineRun.builder()
                .pipeline(pipeline)
                .status("PENDING")
                .build();
        PipelineRun savedRun = pipelineRunRepository.save(run);

        // Start async execution
        executePipelineAsync(savedRun.getId());

        return savedRun.getId();
    }

    @Async
    public void executePipelineAsync(Long runId) {
        PipelineRun run = pipelineRunRepository.findById(runId).orElse(null);
        if (run == null) return;

        Long pipelineId = run.getPipeline().getId();
        String pipelineName = run.getPipeline().getName();

        // Record run start for metrics
        meterRegistry.counter("pipelines.runs.total", "pipeline", pipelineName, "pipelineId", String.valueOf(pipelineId)).increment();
        Timer.Sample sample = Timer.start(meterRegistry);

        try {
            updateRunStatus(run, "RUNNING", null);
            logRun(run, "INFO", "Starting pipeline execution");

            // Get source/target connections
            Connection sourceConn = run.getPipeline().getSourceConnection();
            Connection targetConn = run.getPipeline().getTargetConnection();

            String sourceUrl = buildJdbcUrl(sourceConn);
            String targetUrl = buildJdbcUrl(targetConn);
            String sourcePass = encryptionService.decrypt(sourceConn.getPassword());
            String targetPass = encryptionService.decrypt(targetConn.getPassword());

            logRun(run, "INFO", "Connected to source: " + sourceConn.getHost());

            // Extract from source
            List<Map<String, Object>> rows = extractRows(sourceUrl, sourceConn.getUsername(), sourcePass,
                    run.getPipeline().getSourceTable());
            int extracted = rows.size();
            updateRun(run, extracted, null, null); // partial update
            logRun(run, "INFO", "Extracted " + extracted + " rows from source table");

            logRun(run, "INFO", "Connected to target: " + targetConn.getHost());

            // Insert to target
            int loaded = insertRows(targetUrl, targetConn.getUsername(), targetPass,
                    run.getPipeline().getTargetTable(), rows);
            updateRun(run, null, loaded, null);
            logRun(run, "INFO", "Inserted " + loaded + " rows into target table");

            updateRunStatus(run, "COMPLETED", null);
            logRun(run, "INFO", "Pipeline execution completed successfully");

            // Success metrics
            meterRegistry.counter("pipelines.runs.success", "pipeline", pipelineName, "pipelineId", String.valueOf(pipelineId)).increment();
            long duration = sample.stop(meterRegistry.timer("pipelines.execution.duration", "pipeline", pipelineName));
            meterRegistry.counter("pipelines.rows.transferred", "pipeline", pipelineName, "pipelineId", String.valueOf(pipelineId)).increment(extracted + loaded);
        } catch (Exception e) {
            updateRunStatus(run, "FAILED", e.getMessage());
            logRun(run, "ERROR", "Execution failed: " + e.getMessage());

            // Failure metrics
            meterRegistry.counter("pipelines.runs.failed", "pipeline", pipelineName, "pipelineId", String.valueOf(pipelineId)).increment();
            sample.stop(meterRegistry.timer("pipelines.execution.duration", "pipeline", pipelineName));
        }

        // Check for alerts after run completion/failure
        alertService.checkAndTrigger(run);
    }

    private void updateRunStatus(PipelineRun run, String status, String error) {
        run.setStatus(status);
        if ("COMPLETED".equals(status) || "FAILED".equals(status)) {
            run.setCompletedAt(LocalDateTime.now());
        }
        if (error != null) {
            run.setErrorMessage(error);
        }
        pipelineRunRepository.save(run);
    }

    private void updateRun(PipelineRun run, Integer extracted, Integer loaded, String error) {
        if (extracted != null) run.setRowsExtracted((long) extracted);
        if (loaded != null) run.setRowsLoaded((long) loaded);
        if (error != null) run.setErrorMessage(error);
        pipelineRunRepository.save(run);
    }

    private void logRun(PipelineRun run, String level, String message) {
        PipelineLog log = PipelineLog.builder()
                .pipelineRun(run)
                .logLevel(level)
                .message(message)
                .build();
        pipelineLogRepository.save(log);
    }

    private String buildJdbcUrl(Connection conn) {
        String type = conn.getType().toUpperCase();
        String host = conn.getHost();
        int port = conn.getPort();
        String dbName = conn.getDatabaseName() != null && !conn.getDatabaseName().isEmpty() ? conn.getDatabaseName() : "test";

        return switch (type) {
            case "H2" -> {
                String h = host.toLowerCase();
                if (h.contains("mem")) {
                    yield "jdbc:h2:mem:" + dbName;
                } else if (h.contains("file") || host.startsWith("/") || host.startsWith(".") || port <= 0) {
                    // Support file-based H2: e.g., jdbc:h2:file:/path/to/db or jdbc:h2:file:./data/db
                    String filePath = host.contains(":") ? host : (host.startsWith("/") ? host : "./" + host);
                    yield "jdbc:h2:file:" + filePath + (dbName.equals("test") ? "" : "/" + dbName);
                } else {
                    yield "jdbc:h2:tcp://" + host + ":" + port + "/" + dbName;
                }
            }
            case "MYSQL", "MARIADB" -> "jdbc:mysql://" + host + ":" + port + "/" + dbName;
            case "POSTGRESQL", "POSTGRES" -> "jdbc:postgresql://" + host + ":" + port + "/" + dbName;
            default -> "jdbc:" + type.toLowerCase() + "://" + host + ":" + port + "/" + dbName;
        };
    }

    private List<Map<String, Object>> extractRows(String url, String user, String pass, String table) throws SQLException {
        List<Map<String, Object>> rows = new ArrayList<>();
        try (java.sql.Connection conn = DriverManager.getConnection(url, user, pass);
             Statement stmt = conn.createStatement();
             ResultSet rs = stmt.executeQuery("SELECT * FROM " + table)) {

            ResultSetMetaData meta = rs.getMetaData();
            int colCount = meta.getColumnCount();

            while (rs.next()) {
                Map<String, Object> row = new HashMap<>();
                for (int i = 1; i <= colCount; i++) {
                    row.put(meta.getColumnName(i), rs.getObject(i));
                }
                rows.add(row);
            }
        }
        return rows;
    }

    private int insertRows(String url, String user, String pass, String table, List<Map<String, Object>> rows) throws SQLException {
        if (rows.isEmpty()) return 0;
        try (java.sql.Connection conn = DriverManager.getConnection(url, user, pass)) {
            // Assume first row keys for columns
            Map<String, Object> first = rows.get(0);
            String columns = String.join(",", first.keySet());
            String placeholders = String.join(",", Collections.nCopies(first.size(), "?"));

            String sql = "INSERT INTO " + table + " (" + columns + ") VALUES (" + placeholders + ")";
            try (PreparedStatement pstmt = conn.prepareStatement(sql)) {
                for (Map<String, Object> row : rows) {
                    int idx = 1;
                    for (Object val : row.values()) {
                        pstmt.setObject(idx++, val);
                    }
                    pstmt.addBatch();
                }
                int[] results = pstmt.executeBatch();
                return results.length;
            }
        }
    }

    private PipelineResponse mapToResponse(Pipeline pipeline) {
        return PipelineResponse.builder()
                .id(pipeline.getId())
                .name(pipeline.getName())
                .sourceConnectionId(pipeline.getSourceConnection().getId())
                .sourceTable(pipeline.getSourceTable())
                .targetConnectionId(pipeline.getTargetConnection().getId())
                .targetTable(pipeline.getTargetTable())
                .mappingConfig(pipeline.getMappingConfig())
                .active(pipeline.isActive())
                .createdAt(pipeline.getCreatedAt())
                .updatedAt(pipeline.getUpdatedAt())
                .build();
    }

    // Observability metrics methods
    public PipelineMetricsResponse getOverallMetrics() {
        Long total = pipelineRunRepository.countTotalRuns();
        Long success = pipelineRunRepository.countSuccessfulRuns();
        Long failed = pipelineRunRepository.countFailedRuns();
        Double avgDuration = pipelineRunRepository.getAverageDuration();
        Long totalRows = pipelineRunRepository.getTotalRowsTransferred();
        List<Object[]> statusList = pipelineRunRepository.getStatusCounts();
        LocalDateTime lastRun = pipelineRunRepository.getLastRunAt();

        Map<String, Long> statusCounts = new HashMap<>();
        for (Object[] arr : statusList) {
            statusCounts.put((String) arr[0], (Long) arr[1]);
        }

        return PipelineMetricsResponse.builder()
                .totalRuns(total != null ? total : 0L)
                .successfulRuns(success != null ? success : 0L)
                .failedRuns(failed != null ? failed : 0L)
                .averageDurationSeconds(avgDuration != null ? avgDuration : 0.0)
                .totalRowsTransferred(totalRows != null ? totalRows : 0L)
                .statusCounts(statusCounts)
                .lastRunAt(lastRun)
                .build();
    }

    public PipelineMetricsResponse getPipelineStats(Long pipelineId) {
        // Check pipeline exists
        pipelineRepository.findById(pipelineId)
                .orElseThrow(() -> new EntityNotFoundException("Pipeline not found with id: " + pipelineId));

        Long total = pipelineRunRepository.countTotalRunsForPipeline(pipelineId);
        Long success = pipelineRunRepository.countSuccessfulRunsForPipeline(pipelineId);
        Long failed = pipelineRunRepository.countFailedRunsForPipeline(pipelineId);
        Double avgDuration = pipelineRunRepository.getAverageDurationForPipeline(pipelineId);
        Long totalRows = pipelineRunRepository.getTotalRowsTransferredForPipeline(pipelineId);
        List<Object[]> statusList = pipelineRunRepository.getStatusCountsForPipeline(pipelineId);
        LocalDateTime lastRun = pipelineRunRepository.getLastRunAtForPipeline(pipelineId);

        Map<String, Long> statusCounts = new HashMap<>();
        for (Object[] arr : statusList) {
            statusCounts.put((String) arr[0], (Long) arr[1]);
        }

        return PipelineMetricsResponse.builder()
                .totalRuns(total != null ? total : 0L)
                .successfulRuns(success != null ? success : 0L)
                .failedRuns(failed != null ? failed : 0L)
                .averageDurationSeconds(avgDuration != null ? avgDuration : 0.0)
                .totalRowsTransferred(totalRows != null ? totalRows : 0L)
                .statusCounts(statusCounts)
                .lastRunAt(lastRun)
                .build();
    }

    public List<ExecutionTrendResponse> getExecutionTrends(String granularity, Integer days) {
        if (days == null) days = 7;
        if (granularity == null || granularity.isEmpty()) granularity = "daily";
        List<Object[]> results = pipelineRunRepository.getExecutionTrends(granularity, days);
        return results.stream()
                .map(this::mapToTrendResponse)
                .collect(Collectors.toList());
    }

    private ExecutionTrendResponse mapToTrendResponse(Object[] row) {
        String bucketStr = (String) row[0];
        // Parse based on format from query
        DateTimeFormatter formatter;
        if (bucketStr.contains(":")) {
            formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm");
        } else {
            formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd");
        }
        LocalDateTime timestamp = LocalDateTime.parse(bucketStr, formatter);
        Long total = ((Number) row[1]).longValue();
        Long success = ((Number) row[2]).longValue();
        Long failed = ((Number) row[3]).longValue();
        return ExecutionTrendResponse.builder()
                .timestamp(timestamp)
                .total(total)
                .success(success)
                .failed(failed)
                .build();
    }
}
