package com.datashift.datashift.dto;

import lombok.*;

import java.time.LocalDateTime;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class ExecutionTrendResponse {

    private LocalDateTime timestamp;

    private Long total;

    private Long success;

    private Long failed;
}
