package com.datashift.datashift.controller;

import com.datashift.datashift.dto.AlertResponse;
import com.datashift.datashift.dto.AlertRuleRequest;
import com.datashift.datashift.dto.AlertRuleResponse;
import com.datashift.datashift.service.AlertService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/v1/alerts")
@Tag(name = "Alerts", description = "Alert rules and triggered alerts APIs")
public class AlertController {

    private final AlertService alertService;

    public AlertController(AlertService alertService) {
        this.alertService = alertService;
    }

    // Rules endpoints (under /rules subpath)
    @PostMapping("/rules")
    @Operation(summary = "Create a new alert rule")
    public ResponseEntity<AlertRuleResponse> createRule(@Valid @RequestBody AlertRuleRequest request) {
        AlertRuleResponse response = alertService.createRule(request);
        return new ResponseEntity<>(response, HttpStatus.CREATED);
    }

    @GetMapping("/rules")
    @Operation(summary = "List all alert rules")
    public ResponseEntity<List<AlertRuleResponse>> getAllRules() {
        List<AlertRuleResponse> responses = alertService.getAllRules();
        return ResponseEntity.ok(responses);
    }

    @DeleteMapping("/rules/{id}")
    @Operation(summary = "Delete an alert rule")
    public ResponseEntity<Void> deleteRule(@PathVariable Long id) {
        alertService.deleteRule(id);
        return ResponseEntity.noContent().build();
    }

    // Triggered alerts endpoints
    @GetMapping
    @Operation(summary = "List all triggered alerts (optional filters)")
    public ResponseEntity<List<AlertResponse>> getAllAlerts(
            @RequestParam(required = false) String severity,
            @RequestParam(required = false) Boolean acknowledged) {
        List<AlertResponse> responses = alertService.getAllAlerts(severity, acknowledged);
        return ResponseEntity.ok(responses);
    }

    @GetMapping("/{id}")
    @Operation(summary = "Get specific triggered alert")
    public ResponseEntity<AlertResponse> getAlertById(@PathVariable Long id) {
        AlertResponse response = alertService.getAlertById(id);
        return ResponseEntity.ok(response);
    }

    @PutMapping("/{id}/acknowledge")
    @Operation(summary = "Acknowledge an alert")
    public ResponseEntity<Void> acknowledgeAlert(@PathVariable Long id) {
        alertService.acknowledgeAlert(id);
        return ResponseEntity.ok().build();
    }
}
