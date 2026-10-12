package com.example.farm.repository;

import com.example.farm.model.Goat;
import org.springframework.data.jpa.repository.JpaRepository;

public interface GoatRepository extends JpaRepository<Goat, Long> {

    long countByStableId(Long stableId);
}
