package com.datashift.datashift.dto;

import lombok.*;

import java.time.LocalDateTime;
import java.util.Map;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class PipelineMetricsResponse {
    private Long totalRuns;
    private Long successfulRuns;
    private Long failedRuns;
    private Double averageDurationSeconds;
    private Long totalRowsTransferred;
    private Map<String, Long> statusCounts;
    private LocalDateTime lastRunAt;
}
