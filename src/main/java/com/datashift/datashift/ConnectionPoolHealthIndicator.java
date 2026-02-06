package com.datashift.datashift;

import com.zaxxer.hikari.HikariDataSource;
import org.springframework.boot.actuate.health.Health;
import org.springframework.boot.actuate.health.HealthIndicator;
import org.springframework.stereotype.Component;

import javax.sql.DataSource;

@Component
public class ConnectionPoolHealthIndicator implements HealthIndicator {

    private final DataSource dataSource;

    public ConnectionPoolHealthIndicator(DataSource dataSource) {
        this.dataSource = dataSource;
    }

    @Override
    public Health health() {
        try {
            if (dataSource instanceof HikariDataSource hikari) {
                int active = hikari.getHikariPoolMXBean().getActiveConnections();
                int total = hikari.getHikariPoolMXBean().getTotalConnections();
                int max = hikari.getMaximumPoolSize();
                if (active > max * 0.8) {
                    return Health.down()
                            .withDetail("activeConnections", active)
                            .withDetail("totalConnections", total)
                            .withDetail("maxPoolSize", max)
                            .build();
                }
                return Health.up()
                        .withDetail("activeConnections", active)
                        .withDetail("totalConnections", total)
                        .withDetail("maxPoolSize", max)
                        .build();
            }
            return Health.unknown().withDetail("pool", "unknown type").build();
        } catch (Exception e) {
            return Health.down(e).build();
        }
    }
}
