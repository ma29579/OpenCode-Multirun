package com.example.farm.service;

import com.example.farm.model.Goat;
import com.example.farm.repository.GoatRepository;
import java.util.List;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

@Service
public class GoatService {

    @Autowired
    private GoatRepository goatRepository;

    public List<Goat> getAll() {
        return goatRepository.findAll();
    }

    public Goat getById(Long id) {
        return goatRepository.findById(id).orElse(null);
    }

    public Goat save(Goat goat) {
        long anzahlTiere = goatRepository.countByStableId(goat.getStableId());
        System.out.println("Ziegen im Stall: " + anzahlTiere);
        if (anzahlTiere >= 8) {
            throw new RuntimeException("Stall ist voll");
        }
        return goatRepository.save(goat);
    }

    public void delete(Long id) {
        goatRepository.deleteById(id);
    }
}
