package com.example.farm.repository;

import com.example.farm.model.Horse;
import org.springframework.data.jpa.repository.JpaRepository;

public interface HorseRepository extends JpaRepository<Horse, Long> {

    long countByStableId(Long stableId);
}
