package com.datashift.datashift.repository;

import com.datashift.datashift.model.PipelineRun;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface PipelineRunRepository extends JpaRepository<PipelineRun, Long> {
    Page<PipelineRun> findByPipelineIdOrderByStartedAtDesc(Long pipelineId, Pageable pageable);
}
