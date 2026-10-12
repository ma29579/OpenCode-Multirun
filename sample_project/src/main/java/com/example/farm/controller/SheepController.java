package com.example.farm.controller;

import com.example.farm.model.Sheep;
import com.example.farm.service.SheepService;
import java.util.List;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v1/Sheep")
public class SheepController
{
    private final SheepService sheepService;

    public SheepController(SheepService sheepService)
    {
        this.sheepService = sheepService;
    }

    @GetMapping
    public List<Sheep> list()
    {
        return sheepService.findAll();
    }

    @PostMapping
    public ResponseEntity<?> add(@RequestBody Sheep sheep)
    {
        try
        {
            return sheepService.add(sheep);
        }
        catch (Exception e)
        {
            return ResponseEntity.ok("error: " + e.getMessage());
        }
    }

    @PutMapping("/{id}")
    public ResponseEntity<?> update(@PathVariable Long id, @RequestBody Sheep sheep)
    {
        try
        {
            return sheepService.update(id, sheep);
        }
        catch (Exception e)
        {
            return ResponseEntity.ok("error: " + e.getMessage());
        }
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<?> remove(@PathVariable Long id)
    {
        return sheepService.remove(id);
    }
}
