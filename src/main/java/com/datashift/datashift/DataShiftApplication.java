package com.datashift.datashift;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableAsync;

@SpringBootApplication
@EnableAsync
public class DataShiftApplication {

    public static void main(String[] args) {
        SpringApplication.run(DataShiftApplication.class, args);
    }

}
