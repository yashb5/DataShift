package com.datashift.datashift;

import com.datashift.datashift.model.PipelineRun;
import com.datashift.datashift.repository.PipelineRunRepository;
import org.springframework.boot.actuate.health.Health;
import org.springframework.boot.actuate.health.HealthIndicator;
import org.springframework.stereotype.Component;

import java.time.LocalDateTime;

@Component
public class PipelineHealthIndicator implements HealthIndicator {

    private final PipelineRunRepository pipelineRunRepository;

    public PipelineHealthIndicator(PipelineRunRepository pipelineRunRepository) {
        this.pipelineRunRepository = pipelineRunRepository;
    }

    @Override
    public Health health() {
        try {
            LocalDateTime since = LocalDateTime.now().minusHours(24);
            long recentFailures = countRecentFailures(since);
            if (recentFailures > 5) {
                return Health.down().withDetail("recentFailures", recentFailures).build();
            }
            return Health.up().withDetail("recentFailures", recentFailures).build();
        } catch (Exception e) {
            return Health.down(e).build();
        }
    }

    private long countRecentFailures(LocalDateTime since) {
        return pipelineRunRepository.findAll().stream()
                .filter(run -> "FAILED".equals(run.getStatus()) && run.getStartedAt() != null && run.getStartedAt().isAfter(since))
                .count();
    }
}
