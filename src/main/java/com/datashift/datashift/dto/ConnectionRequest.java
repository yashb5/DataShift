package com.datashift.datashift.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import lombok.*;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class ConnectionRequest {

    @NotBlank
    @Size(max = 100)
    private String name;

    @NotBlank
    @Size(max = 50)
    private String type;

    @NotBlank
    @Size(max = 255)
    private String host;

    @NotNull
    private Integer port;

    @NotBlank
    @Size(max = 100)
    private String username;

    @NotBlank
    @Size(max = 255)
    private String password;

    @Size(max = 100)
    private String databaseName;
}
