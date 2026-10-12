package com.example.farm.repository;

import com.example.farm.model.Rabbit;
import org.springframework.data.jpa.repository.JpaRepository;

public interface RabbitRepository extends JpaRepository<Rabbit, Long> {

    long countByStableId(Long stableId);
}
