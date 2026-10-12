package com.example.farm.repository;

import com.example.farm.model.Stable;
import org.springframework.data.jpa.repository.JpaRepository;

public interface StableRepository extends JpaRepository<Stable, Long> {
}
