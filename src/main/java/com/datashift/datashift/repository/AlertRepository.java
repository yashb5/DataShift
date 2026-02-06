package com.datashift.datashift.repository;

import com.datashift.datashift.model.Alert;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface AlertRepository extends JpaRepository<Alert, Long> {

    List<Alert> findBySeverity(String severity);

    List<Alert> findByAcknowledged(boolean acknowledged);

    List<Alert> findBySeverityAndAcknowledged(String severity, boolean acknowledged);
}
