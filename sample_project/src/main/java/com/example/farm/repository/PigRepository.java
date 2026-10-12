package com.example.farm.repository;

import com.example.farm.model.Pig;
import org.springframework.data.jpa.repository.JpaRepository;

public interface PigRepository extends JpaRepository<Pig, Integer> {

    long countByStableId(Long stableId);
}
