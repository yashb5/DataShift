package com.datashift.datashift.dto;

import lombok.*;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class ColumnInfo {

    private String name;
    private String type;
    private boolean nullable;
}
