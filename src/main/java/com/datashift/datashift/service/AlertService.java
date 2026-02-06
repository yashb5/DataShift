package com.datashift.datashift.service;

import com.datashift.datashift.dto.AlertResponse;
import com.datashift.datashift.dto.AlertRuleRequest;
import com.datashift.datashift.dto.AlertRuleResponse;
import com.datashift.datashift.model.Alert;
import com.datashift.datashift.model.AlertRule;
import com.datashift.datashift.model.PipelineRun;
import com.datashift.datashift.repository.AlertRepository;
import com.datashift.datashift.repository.AlertRuleRepository;
import com.datashift.datashift.repository.PipelineRunRepository;
import jakarta.persistence.EntityNotFoundException;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;
import java.util.stream.Collectors;

@Service
@Transactional
public class AlertService {

    private final AlertRuleRepository alertRuleRepository;
    private final AlertRepository alertRepository;
    private final PipelineRunRepository pipelineRunRepository;  // for checks

    public AlertService(AlertRuleRepository alertRuleRepository, AlertRepository alertRepository,
                        PipelineRunRepository pipelineRunRepository) {
        this.alertRuleRepository = alertRuleRepository;
        this.alertRepository = alertRepository;
        this.pipelineRunRepository = pipelineRunRepository;
    }

    public AlertRuleResponse createRule(AlertRuleRequest request) {
        AlertRule rule = AlertRule.builder()
                .name(request.getName())
                .description(request.getDescription())
                .conditionType(request.getConditionType())
                .pipelineId(request.getPipelineId())
                .threshold(request.getThreshold())
                .timeWindowHours(request.getTimeWindowHours())
                .severity(request.getSeverity())
                .build();
        AlertRule saved = alertRuleRepository.save(rule);
        return mapToRuleResponse(saved);
    }

    public List<AlertRuleResponse> getAllRules() {
        return alertRuleRepository.findAll().stream()
                .map(this::mapToRuleResponse)
                .collect(Collectors.toList());
    }

    public void deleteRule(Long id) {
        if (!alertRuleRepository.existsById(id)) {
            throw new EntityNotFoundException("Alert rule not found with id: " + id);
        }
        alertRuleRepository.deleteById(id);
    }

    public void checkAndTrigger(PipelineRun run) {
        LocalDateTime now = LocalDateTime.now();
        List<AlertRule> rules = alertRuleRepository.findByPipelineIdOrPipelineIdIsNull(run.getPipeline().getId());
        for (AlertRule rule : rules) {
            if (matchesRule(rule, run, now)) {
                triggerAlert(rule, run);
            }
        }
    }

    private boolean matchesRule(AlertRule rule, PipelineRun run, LocalDateTime now) {
        LocalDateTime windowStart = now.minusHours(rule.getTimeWindowHours());
        switch (rule.getConditionType()) {
            case "FAILED_COUNT":
                long failures = pipelineRunRepository.findAll().stream()
                        .filter(r -> (rule.getPipelineId() == null || r.getPipeline().getId().equals(rule.getPipelineId()))
                                && "FAILED".equals(r.getStatus()) && r.getStartedAt() != null && r.getStartedAt().isAfter(windowStart))
                        .count();
                return failures >= rule.getThreshold();
            case "NO_SUCCESS":
                long successes = pipelineRunRepository.findAll().stream()
                        .filter(r -> (rule.getPipelineId() == null || r.getPipeline().getId().equals(rule.getPipelineId()))
                                && "COMPLETED".equals(r.getStatus()) && r.getStartedAt() != null && r.getStartedAt().isAfter(windowStart))
                        .count();
                return successes == 0;
            case "AVG_DURATION":
                // Simple avg calc
                double avg = pipelineRunRepository.findAll().stream()
                        .filter(r -> (rule.getPipelineId() == null || r.getPipeline().getId().equals(rule.getPipelineId()))
                                && r.getCompletedAt() != null && r.getStartedAt() != null && r.getStartedAt().isAfter(windowStart))
                        .mapToLong(r -> java.time.Duration.between(r.getStartedAt(), r.getCompletedAt()).getSeconds())
                        .average().orElse(0.0);
                return avg > rule.getThreshold() * 60;  // threshold in minutes
            default:
                return false;
        }
    }

    private void triggerAlert(AlertRule rule, PipelineRun run) {
        String message = "Alert triggered for rule '" + rule.getName() + "' on pipeline " + run.getPipeline().getName();
        Alert alert = Alert.builder()
                .rule(rule)
                .message(message)
                .severity(rule.getSeverity())
                .build();
        alertRepository.save(alert);
    }

    private AlertRuleResponse mapToRuleResponse(AlertRule rule) {
        return AlertRuleResponse.builder()
                .id(rule.getId())
                .name(rule.getName())
                .description(rule.getDescription())
                .conditionType(rule.getConditionType())
                .pipelineId(rule.getPipelineId())
                .threshold(rule.getThreshold())
                .timeWindowHours(rule.getTimeWindowHours())
                .severity(rule.getSeverity())
                .createdAt(rule.getCreatedAt())
                .build();
    }

    // Alert methods for triggered alerts
    public List<AlertResponse> getAllAlerts(String severity, Boolean acknowledged) {
        List<Alert> alerts;
        if (severity != null && acknowledged != null) {
            alerts = alertRepository.findBySeverityAndAcknowledged(severity, acknowledged);
        } else if (severity != null) {
            alerts = alertRepository.findBySeverity(severity);
        } else if (acknowledged != null) {
            alerts = alertRepository.findByAcknowledged(acknowledged);
        } else {
            alerts = alertRepository.findAll();
        }
        return alerts.stream()
                .map(this::mapToAlertResponse)
                .collect(Collectors.toList());
    }

    public AlertResponse getAlertById(Long id) {
        Alert alert = alertRepository.findById(id)
                .orElseThrow(() -> new EntityNotFoundException("Alert not found with id: " + id));
        return mapToAlertResponse(alert);
    }

    public void acknowledgeAlert(Long id) {
        Alert alert = alertRepository.findById(id)
                .orElseThrow(() -> new EntityNotFoundException("Alert not found with id: " + id));
        alert.setAcknowledged(true);
        alertRepository.save(alert);
    }

    private AlertResponse mapToAlertResponse(Alert alert) {
        return AlertResponse.builder()
                .id(alert.getId())
                .ruleId(alert.getRule().getId())
                .message(alert.getMessage())
                .severity(alert.getSeverity())
                .acknowledged(alert.isAcknowledged())
                .triggeredAt(alert.getTriggeredAt())
                .build();
    }
}
