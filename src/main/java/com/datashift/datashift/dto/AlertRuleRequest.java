package com.datashift.datashift.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.*;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class AlertRuleRequest {

    @NotBlank
    private String name;

    private String description;

    @NotBlank
    private String conditionType;

    private Long pipelineId;

    @NotNull
    private Integer threshold;

    @NotNull
    private Integer timeWindowHours;

    @NotBlank
    private String severity;
}
