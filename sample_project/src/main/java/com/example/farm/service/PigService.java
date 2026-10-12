package com.example.farm.service;

import com.example.farm.model.Pig;
import com.example.farm.repository.PigRepository;
import java.util.List;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

@Service
public class PigService {

    @Autowired
    private PigRepository pigRepository;

    public List<Pig> findAll() {
        return pigRepository.findAll();
    }

    /**
     * Returns the pig with the given id.
     */
    public int fatteningDays(Pig p) {
        double x = p.getTargetWeightKg() - 25.0;
        return (int) Math.ceil(x / 0.75);
    }
}
