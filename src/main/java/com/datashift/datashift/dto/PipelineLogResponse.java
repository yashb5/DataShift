package com.datashift.datashift.dto;

import lombok.*;

import java.time.LocalDateTime;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class PipelineLogResponse {

    private Long id;
    private Long pipelineRunId;
    private LocalDateTime timestamp;
    private String logLevel;
    private String message;
}
