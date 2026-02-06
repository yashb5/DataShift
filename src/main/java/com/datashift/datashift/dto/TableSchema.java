package com.datashift.datashift.dto;

import lombok.*;

import java.util.List;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class TableSchema {

    private String name;
    private List<ColumnInfo> columns;
}
