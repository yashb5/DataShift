package com.datashift.datashift.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import lombok.*;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class PipelineRequest {

    @NotBlank
    @Size(max = 100)
    private String name;

    @NotNull
    private Long sourceConnectionId;

    @NotBlank
    @Size(max = 100)
    private String sourceTable;

    @NotNull
    private Long targetConnectionId;

    @NotBlank
    @Size(max = 100)
    private String targetTable;

    private String mappingConfig;
}
