package com.datashift.datashift.dto;

import lombok.*;

import java.time.LocalDateTime;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class PipelineRunResponse {

    private Long id;
    private Long pipelineId;
    private LocalDateTime startedAt;
    private LocalDateTime completedAt;
    private Long rowsExtracted;
    private Long rowsLoaded;
    private String status;
    private String errorMessage;
    private LocalDateTime createdAt;
}
