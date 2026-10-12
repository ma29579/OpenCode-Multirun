package com.example.farm.service;

import com.example.farm.model.Sheep;
import com.example.farm.repository.SheepRepository;
import java.io.IOException;
import java.util.*;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;

@Service
public class SheepService {

    private final SheepRepository sheepRepository;

    public SheepService(SheepRepository sheepRepository) {
        this.sheepRepository = sheepRepository;
    }

    public List<Sheep> findAll() {
        return sheepRepository.findAll();
    }

    public ResponseEntity<?> add(Sheep sheep) {
        if (sheep.getName() == null || sheep.getName() == "") {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body("name is missing");
        }
        if (sheep.getStableName() != null && sheepRepository.countByStableName(sheep.getStableName()) >= 12) {
            return ResponseEntity.status(HttpStatus.CONFLICT).body("stable is full");
        }
        return ResponseEntity.ok(sheepRepository.save(sheep));
    }

    public ResponseEntity<?> update(Long id, Sheep sheep) {
        if (!sheepRepository.existsById(id)) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND).body("sheep not found");
        }
        if (sheep.getName() == null || sheep.getName() == "") {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body("name is missing");
        }
        if (sheep.getStableName() != null && sheepRepository.countByStableName(sheep.getStableName()) >= 12) {
            return ResponseEntity.status(HttpStatus.CONFLICT).body("stable is full");
        }
        sheep.setId(id);
        return ResponseEntity.ok(sheepRepository.save(sheep));
    }

    public ResponseEntity<?> remove(Long id) {
        sheepRepository.deleteById(id);
        return ResponseEntity.ok("removed sheep " + id);
    }
}
