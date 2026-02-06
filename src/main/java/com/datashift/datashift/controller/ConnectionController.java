package com.datashift.datashift.controller;

import com.datashift.datashift.dto.ConnectionRequest;
import com.datashift.datashift.dto.ConnectionResponse;
import com.datashift.datashift.dto.ConnectionTestResponse;
import com.datashift.datashift.dto.TableSchema;
import com.datashift.datashift.service.ConnectionService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/v1/connections")
@Tag(name = "Connections", description = "Connection management APIs")
public class ConnectionController {

    private final ConnectionService connectionService;

    public ConnectionController(ConnectionService connectionService) {
        this.connectionService = connectionService;
    }

    @PostMapping
    @Operation(summary = "Create a new database connection")
    public ResponseEntity<ConnectionResponse> createConnection(@Valid @RequestBody ConnectionRequest request) {
        ConnectionResponse response = connectionService.createConnection(request);
        return new ResponseEntity<>(response, HttpStatus.CREATED);
    }

    @GetMapping
    @Operation(summary = "List all connections")
    public ResponseEntity<List<ConnectionResponse>> getAllConnections() {
        List<ConnectionResponse> responses = connectionService.getAllConnections();
        return ResponseEntity.ok(responses);
    }

    @GetMapping("/{id}")
    @Operation(summary = "Get connection by ID")
    public ResponseEntity<ConnectionResponse> getConnectionById(@PathVariable Long id) {
        ConnectionResponse response = connectionService.getConnectionById(id);
        return ResponseEntity.ok(response);
    }

    @DeleteMapping("/{id}")
    @Operation(summary = "Delete a connection")
    public ResponseEntity<Void> deleteConnection(@PathVariable Long id) {
        connectionService.deleteConnection(id);
        return ResponseEntity.noContent().build();
    }

    @PostMapping("/{id}/test")
    @Operation(summary = "Test connection to database")
    public ResponseEntity<ConnectionTestResponse> testConnection(@PathVariable Long id) {
        ConnectionTestResponse response = connectionService.testConnection(id);
        return ResponseEntity.ok(response);
    }

    @GetMapping("/{id}/schemas")
    @Operation(summary = "Get database schemas and tables/columns")
    public ResponseEntity<List<TableSchema>> getSchemas(@PathVariable Long id) {
        List<TableSchema> schemas = connectionService.getSchemas(id);
        return ResponseEntity.ok(schemas);
    }
}
