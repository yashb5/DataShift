package com.datashift.datashift.dto;

import lombok.*;

import java.time.LocalDateTime;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class ConnectionResponse {

    private Long id;
    private String name;
    private String type;
    private String host;
    private Integer port;
    private String username;
    private String databaseName;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
    // Note: password omitted for security
}
