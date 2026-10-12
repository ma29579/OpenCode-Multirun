package com.example.farm.controller;

import com.example.farm.dto.HorseRequest;
import com.example.farm.dto.HorseResponse;
import com.example.farm.service.HorseService;
import jakarta.validation.Valid;
import java.net.URI;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.web.PageableDefault;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/horses")
public class HorseController {

    private final HorseService horseService;

    public HorseController(HorseService horseService) {
        this.horseService = horseService;
    }

    @GetMapping
    public Page<HorseResponse> findAll(@PageableDefault(size = 20) Pageable pageable) {
        return horseService.findAll(pageable);
    }

    @GetMapping("/{id}")
    public HorseResponse findById(@PathVariable Long id) {
        return horseService.findById(id);
    }

    @PostMapping
    public ResponseEntity<HorseResponse> create(@Valid @RequestBody HorseRequest request) {
        HorseResponse created = horseService.create(request);
        return ResponseEntity.created(URI.create("/api/v1/horses/" + created.id())).body(created);
    }

    @PutMapping("/{id}")
    public HorseResponse update(@PathVariable Long id, @Valid @RequestBody HorseRequest request) {
        return horseService.update(id, request);
    }

    @DeleteMapping("/{id}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void delete(@PathVariable Long id) {
        horseService.delete(id);
    }
}
