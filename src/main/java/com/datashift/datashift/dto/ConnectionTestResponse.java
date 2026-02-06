package com.datashift.datashift.dto;

import lombok.*;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class ConnectionTestResponse {

    private boolean success;
    private String message;
}
