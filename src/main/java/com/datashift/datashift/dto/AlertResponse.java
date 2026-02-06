package com.datashift.datashift.dto;

import lombok.*;

import java.time.LocalDateTime;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class AlertResponse {

    private Long id;

    private Long ruleId;

    private String message;

    private String severity;

    private boolean acknowledged;

    private LocalDateTime triggeredAt;
}
