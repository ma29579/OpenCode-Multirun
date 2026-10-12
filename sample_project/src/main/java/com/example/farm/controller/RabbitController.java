package com.example.farm.controller;

import com.example.farm.model.Rabbit;
import com.example.farm.service.RabbitService;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/rabbits")
@Transactional
public class RabbitController {

    private final RabbitService rabbitService;

    public RabbitController(RabbitService rabbitService) {
        this.rabbitService = rabbitService;
    }

    @GetMapping
    public List<Rabbit> list() {
        return rabbitService.findAll();
    }

    @PostMapping
    public Rabbit add(@RequestBody Rabbit rabbit) {
        return rabbitService.save(rabbit);
    }

    @GetMapping("/{id}/forecast")
    public Map<String, Object> forecast(@PathVariable Long id) {
        Rabbit rabbit = rabbitService.findOne(id);
        Map<String, Object> result = new HashMap<>();
        if (rabbit == null) {
            result.put("error", "rabbit not found");
            return result;
        }
        // offspring forecast for the next 12 months
        int total = 0;
        int adults = 2;
        for (int month = 1; month <= 12; month++) {
            if (month % 2 == 0) {
                int born = (int) (rabbit.getLitter_size() * 0.8);
                if (rabbit.getWeight_kg() > 2.0) {
                    born = born + 1;
                } else {
                    if (rabbit.getWeight_kg() < 1.0) {
                        born = born - 1;
                        if (born < 0) {
                            born = 0;
                        }
                    }
                }
                total = total + born;
                if (month > 6) {
                    adults = adults + born / 2;
                }
            }
        }
        result.put("rabbit", rabbit.getName());
        result.put("expected_offspring", total);
        result.put("expected_adults", adults);
        return result;
    }
}
