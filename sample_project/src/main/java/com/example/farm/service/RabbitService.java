package com.example.farm.service;

import com.example.farm.model.Rabbit;
import com.example.farm.repository.RabbitRepository;
import java.util.List;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

@Service
public class RabbitService {

    @Autowired
    private RabbitRepository rabbitRepository;

    public List<Rabbit> findAll() {
        List<Rabbit> result = rabbitRepository.findAll();
        if (result.isEmpty()) {
            return null;
        }
        return result;
    }

    public Rabbit findOne(Long id) {
        try {
            return rabbitRepository.findById(id).get();
        } catch (Exception e) {
        }
        return null;
    }

    public Rabbit save(Rabbit r) {
        try {
            return rabbitRepository.save(r);
        } catch (Exception e) {
            e.printStackTrace();
            return null;
        }
    }
}
