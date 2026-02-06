package com.datashift.datashift.model;

import jakarta.persistence.*;
import lombok.*;

import java.time.LocalDateTime;

@Entity
@Table(name = "pipeline_logs")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class PipelineLog {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "pipeline_run_id")
    private PipelineRun pipelineRun;

    @Column(name = "timestamp")
    private LocalDateTime timestamp;

    @Column(name = "log_level")
    private String logLevel; // INFO, ERROR, etc.

    @Column(name = "message", columnDefinition = "TEXT")
    private String message;

    @PrePersist
    protected void onCreate() {
        if (timestamp == null) {
            timestamp = LocalDateTime.now();
        }
    }
}
