package com.datashift.datashift.service;

import com.datashift.datashift.dto.ColumnInfo;
import com.datashift.datashift.dto.ConnectionRequest;
import com.datashift.datashift.dto.ConnectionResponse;
import com.datashift.datashift.dto.ConnectionTestResponse;
import com.datashift.datashift.dto.TableSchema;
import com.datashift.datashift.model.Connection;
import com.datashift.datashift.repository.ConnectionRepository;
import jakarta.persistence.EntityNotFoundException;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.sql.*;
import java.util.ArrayList;
import java.util.List;
import java.util.stream.Collectors;

@Service
@Transactional
public class ConnectionService {

    private final ConnectionRepository connectionRepository;
    private final EncryptionService encryptionService;

    public ConnectionService(ConnectionRepository connectionRepository, EncryptionService encryptionService) {
        this.connectionRepository = connectionRepository;
        this.encryptionService = encryptionService;
    }

    public ConnectionResponse createConnection(ConnectionRequest request) {
        if (connectionRepository.findByName(request.getName()).isPresent()) {
            throw new IllegalArgumentException("Connection with name '" + request.getName() + "' already exists");
        }

        String encryptedPassword = encryptionService.encrypt(request.getPassword());

        Connection connection = Connection.builder()
                .name(request.getName())
                .type(request.getType())
                .host(request.getHost())
                .port(request.getPort())
                .username(request.getUsername())
                .password(encryptedPassword)
                .databaseName(request.getDatabaseName())
                .build();

        Connection saved = connectionRepository.save(connection);
        return mapToResponse(saved);
    }

    public List<ConnectionResponse> getAllConnections() {
        return connectionRepository.findAll().stream()
                .map(this::mapToResponse)
                .collect(Collectors.toList());
    }

    public ConnectionResponse getConnectionById(Long id) {
        Connection connection = connectionRepository.findById(id)
                .orElseThrow(() -> new EntityNotFoundException("Connection not found with id: " + id));
        return mapToResponse(connection);
    }

    public void deleteConnection(Long id) {
        if (!connectionRepository.existsById(id)) {
            throw new EntityNotFoundException("Connection not found with id: " + id);
        }
        connectionRepository.deleteById(id);
    }

    public ConnectionTestResponse testConnection(Long id) {
        Connection connection = connectionRepository.findById(id)
                .orElseThrow(() -> new EntityNotFoundException("Connection not found with id: " + id));

        String decryptedPassword = encryptionService.decrypt(connection.getPassword());
        String jdbcUrl = buildJdbcUrl(connection);

        try (java.sql.Connection dbConnection = DriverManager.getConnection(jdbcUrl, connection.getUsername(), decryptedPassword)) {
            return ConnectionTestResponse.builder()
                    .success(true)
                    .message("Connection successful")
                    .build();
        } catch (Exception e) {
            return ConnectionTestResponse.builder()
                    .success(false)
                    .message("Connection failed: " + e.getMessage())
                    .build();
        }
    }

    private String buildJdbcUrl(Connection conn) {
        String type = conn.getType().toUpperCase();
        String host = conn.getHost();
        int port = conn.getPort();
        String dbName = conn.getDatabaseName() != null && !conn.getDatabaseName().isEmpty() ? conn.getDatabaseName() : "test";

        return switch (type) {
            case "H2" -> {
                String h = host.toLowerCase();
                if (h.contains("mem")) {
                    yield "jdbc:h2:mem:" + dbName;
                } else if (h.contains("file") || host.startsWith("/") || host.startsWith(".") || port <= 0) {
                    // Support file-based H2: e.g., jdbc:h2:file:/path/to/db or jdbc:h2:file:./data/db
                    String filePath = host.contains(":") ? host : (host.startsWith("/") ? host : "./" + host);
                    yield "jdbc:h2:file:" + filePath + (dbName.equals("test") ? "" : "/" + dbName);
                } else {
                    yield "jdbc:h2:tcp://" + host + ":" + port + "/" + dbName;
                }
            }
            case "MYSQL", "MARIADB" -> "jdbc:mysql://" + host + ":" + port + "/" + dbName;
            case "POSTGRESQL", "POSTGRES" -> "jdbc:postgresql://" + host + ":" + port + "/" + dbName;
            default -> "jdbc:" + type.toLowerCase() + "://" + host + ":" + port + "/" + dbName;
        };
    }

    public List<TableSchema> getSchemas(Long id) {
        Connection connection = connectionRepository.findById(id)
                .orElseThrow(() -> new EntityNotFoundException("Connection not found with id: " + id));

        String decryptedPassword = encryptionService.decrypt(connection.getPassword());
        String jdbcUrl = buildJdbcUrl(connection);

        List<TableSchema> schemas = new ArrayList<>();
        try (java.sql.Connection dbConnection = DriverManager.getConnection(jdbcUrl, connection.getUsername(), decryptedPassword)) {
            DatabaseMetaData metaData = dbConnection.getMetaData();
            ResultSet tables = metaData.getTables(null, null, "%", new String[]{"TABLE"});

            while (tables.next()) {
                String tableName = tables.getString("TABLE_NAME");
                List<ColumnInfo> columns = new ArrayList<>();

                ResultSet cols = metaData.getColumns(null, null, tableName, "%");
                while (cols.next()) {
                    String colName = cols.getString("COLUMN_NAME");
                    String colType = cols.getString("TYPE_NAME");
                    boolean nullable = cols.getInt("NULLABLE") != DatabaseMetaData.columnNoNulls;
                    columns.add(ColumnInfo.builder()
                            .name(colName)
                            .type(colType)
                            .nullable(nullable)
                            .build());
                }
                cols.close();

                schemas.add(TableSchema.builder()
                        .name(tableName)
                        .columns(columns)
                        .build());
            }
            tables.close();
        } catch (Exception e) {
            throw new RuntimeException("Failed to fetch schema: " + e.getMessage(), e);
        }
        return schemas;
    }

    private ConnectionResponse mapToResponse(Connection connection) {
        return ConnectionResponse.builder()
                .id(connection.getId())
                .name(connection.getName())
                .type(connection.getType())
                .host(connection.getHost())
                .port(connection.getPort())
                .username(connection.getUsername())
                .databaseName(connection.getDatabaseName())
                .createdAt(connection.getCreatedAt())
                .updatedAt(connection.getUpdatedAt())
                .build();
    }
}
