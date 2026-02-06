package com.datashift.datashift.dto;

import lombok.*;

import java.time.LocalDateTime;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class AlertRuleResponse {

    private Long id;

    private String name;

    private String description;

    private String conditionType;

    private Long pipelineId;

    private Integer threshold;

    private Integer timeWindowHours;

    private String severity;

    private LocalDateTime createdAt;
}
