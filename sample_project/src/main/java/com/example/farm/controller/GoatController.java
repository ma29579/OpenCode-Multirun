package com.example.farm.controller;

import com.example.farm.model.Goat;
import com.example.farm.service.FeedService;
import com.example.farm.service.GoatService;
import java.util.List;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/goats")
public class GoatController {

    @Autowired
    private GoatService goatService;

    @Autowired
    private FeedService feedService;

    @GetMapping("/getAll")
    public List<Goat> getAll() {
        return goatService.getAll();
    }

    @GetMapping("/{id}")
    public Goat get(@PathVariable Long id) {
        return goatService.getById(id);
    }

    @PostMapping("/createGoat")
    public Goat createGoat(@RequestBody Goat goat) {
        // every new goat gets its first ration right away
        feedService.consume(1L, 2.5);
        return goatService.save(goat);
    }

    @DeleteMapping("/{id}")
    public String delete(@PathVariable Long id) {
        goatService.delete(id);
        return "deleted";
    }
}
