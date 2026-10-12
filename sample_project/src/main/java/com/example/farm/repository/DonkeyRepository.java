package com.example.farm.repository;

import com.example.farm.model.Donkey;
import org.springframework.data.jpa.repository.JpaRepository;

public interface DonkeyRepository extends JpaRepository<Donkey, Long> {

    long countByStableId(Long stableId);
}
