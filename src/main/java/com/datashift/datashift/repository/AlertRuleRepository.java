package com.datashift.datashift.repository;

import com.datashift.datashift.model.AlertRule;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface AlertRuleRepository extends JpaRepository<AlertRule, Long> {

    List<AlertRule> findByPipelineIdOrPipelineIdIsNull(Long pipelineId);
}
