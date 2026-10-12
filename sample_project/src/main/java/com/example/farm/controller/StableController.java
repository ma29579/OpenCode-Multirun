package com.example.farm.controller;

import com.example.farm.dto.StableRequest;
import com.example.farm.dto.StableResponse;
import com.example.farm.service.StableService;
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
@RequestMapping("/api/v1/stables")
public class StableController {

    private final StableService stableService;

    public StableController(StableService stableService) {
        this.stableService = stableService;
    }

    @GetMapping
    public Page<StableResponse> findAll(@PageableDefault(size = 20) Pageable pageable) {
        return stableService.findAll(pageable);
    }

    @GetMapping("/{id}")
    public StableResponse findById(@PathVariable Long id) {
        return stableService.findById(id);
    }

    @PostMapping
    public ResponseEntity<StableResponse> create(@Valid @RequestBody StableRequest request) {
        StableResponse created = stableService.create(request);
        return ResponseEntity.created(URI.create("/api/v1/stables/" + created.id())).body(created);
    }

    @PutMapping("/{id}")
    public StableResponse update(@PathVariable Long id, @Valid @RequestBody StableRequest request) {
        return stableService.update(id, request);
    }

    @DeleteMapping("/{id}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void delete(@PathVariable Long id) {
        stableService.delete(id);
    }
}
