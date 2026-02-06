package com.datashift.datashift.repository;

import com.datashift.datashift.model.PipelineRun;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;

@Repository
public interface PipelineRunRepository extends JpaRepository<PipelineRun, Long> {
    Page<PipelineRun> findByPipelineIdOrderByStartedAtDesc(Long pipelineId, Pageable pageable);

    // Aggregate queries for metrics (native for avg duration to ensure H2 compatibility)
    @Query("SELECT COUNT(r) FROM PipelineRun r")
    Long countTotalRuns();

    @Query("SELECT COUNT(r) FROM PipelineRun r WHERE r.status = 'COMPLETED'")
    Long countSuccessfulRuns();

    @Query("SELECT COUNT(r) FROM PipelineRun r WHERE r.status = 'FAILED'")
    Long countFailedRuns();

    @Query(value = "SELECT AVG(DATEDIFF('SECOND', started_at, completed_at)) FROM pipeline_runs WHERE completed_at IS NOT NULL", nativeQuery = true)
    Double getAverageDuration();

    @Query("SELECT COALESCE(SUM(r.rowsLoaded), 0) FROM PipelineRun r")
    Long getTotalRowsTransferred();

    @Query("SELECT r.status, COUNT(r) FROM PipelineRun r GROUP BY r.status")
    List<Object[]> getStatusCounts();

    @Query("SELECT MAX(r.startedAt) FROM PipelineRun r")
    LocalDateTime getLastRunAt();

    // Per-pipeline variants
    @Query("SELECT COUNT(r) FROM PipelineRun r WHERE r.pipeline.id = :pipelineId")
    Long countTotalRunsForPipeline(@Param("pipelineId") Long pipelineId);

    @Query("SELECT COUNT(r) FROM PipelineRun r WHERE r.pipeline.id = :pipelineId AND r.status = 'COMPLETED'")
    Long countSuccessfulRunsForPipeline(@Param("pipelineId") Long pipelineId);

    @Query("SELECT COUNT(r) FROM PipelineRun r WHERE r.pipeline.id = :pipelineId AND r.status = 'FAILED'")
    Long countFailedRunsForPipeline(@Param("pipelineId") Long pipelineId);

    @Query(value = "SELECT AVG(DATEDIFF('SECOND', started_at, completed_at)) FROM pipeline_runs WHERE pipeline_id = :pipelineId AND completed_at IS NOT NULL", nativeQuery = true)
    Double getAverageDurationForPipeline(@Param("pipelineId") Long pipelineId);

    @Query("SELECT COALESCE(SUM(r.rowsLoaded), 0) FROM PipelineRun r WHERE r.pipeline.id = :pipelineId")
    Long getTotalRowsTransferredForPipeline(@Param("pipelineId") Long pipelineId);

    @Query("SELECT r.status, COUNT(r) FROM PipelineRun r WHERE r.pipeline.id = :pipelineId GROUP BY r.status")
    List<Object[]> getStatusCountsForPipeline(@Param("pipelineId") Long pipelineId);

    @Query("SELECT MAX(r.startedAt) FROM PipelineRun r WHERE r.pipeline.id = :pipelineId")
    LocalDateTime getLastRunAtForPipeline(@Param("pipelineId") Long pipelineId);

    // Trends query using H2 date functions for grouping by granularity
    @Query(value = """
        SELECT 
            CASE 
                WHEN :granularity = 'hourly' THEN FORMATDATETIME(started_at, 'yyyy-MM-dd HH:00')
                WHEN :granularity = 'daily' THEN FORMATDATETIME(started_at, 'yyyy-MM-dd')
                ELSE FORMATDATETIME(started_at, 'yyyy-MM-dd') 
            END as bucket,
            COUNT(*) as total,
            SUM(CASE WHEN status = 'COMPLETED' THEN 1 ELSE 0 END) as success,
            SUM(CASE WHEN status = 'FAILED' THEN 1 ELSE 0 END) as failed
        FROM pipeline_runs 
        WHERE started_at >= DATEADD('DAY', - :days, CURRENT_TIMESTAMP())
        GROUP BY bucket
        ORDER BY bucket
        """, nativeQuery = true)
    List<Object[]> getExecutionTrends(@Param("granularity") String granularity, @Param("days") Integer days);
}
