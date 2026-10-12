package com.example.farm.repository;

import com.example.farm.model.Sheep;
import org.springframework.data.jpa.repository.JpaRepository;

public interface SheepRepository extends JpaRepository<Sheep, Long> {

    long countByStableName(String stableName);
}
