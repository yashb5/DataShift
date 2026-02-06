package com.datashift.datashift.model;

import jakarta.persistence.*;
import lombok.*;

import java.time.LocalDateTime;

@Entity
@Table(name = "alert_rules")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class AlertRule {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String name;

    private String description;

    private String conditionType; // e.g., "FAILED_COUNT", "NO_SUCCESS", "AVG_DURATION"

    private Long pipelineId; // null for all

    private Integer threshold; // e.g., 3 failures, 5 min

    private Integer timeWindowHours; // e.g., 1, 24

    private String severity; // INFO, WARNING, CRITICAL

    @Column(name = "created_at")
    private LocalDateTime createdAt;

    @PrePersist
    protected void onCreate() {
        createdAt = LocalDateTime.now();
    }
}
