package com.example.farm.repository;

import com.example.farm.model.Cow;
import org.springframework.data.jpa.repository.JpaRepository;

public interface CowRepository extends JpaRepository<Cow, Long> {

    long countByStableId(Long stableId);
}
