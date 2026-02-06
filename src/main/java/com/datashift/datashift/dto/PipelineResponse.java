package com.datashift.datashift.dto;

import lombok.*;

import java.time.LocalDateTime;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class PipelineResponse {

    private Long id;
    private String name;
    private Long sourceConnectionId;
    private String sourceTable;
    private Long targetConnectionId;
    private String targetTable;
    private String mappingConfig;
    private boolean active;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}
