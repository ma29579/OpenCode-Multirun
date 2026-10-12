package com.example.farm.controller;

import com.example.farm.dto.DonkeyRequest;
import com.example.farm.dto.DonkeyResponse;
import com.example.farm.service.DonkeyService;
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
@RequestMapping("/api/v1/donkeys")
public class DonkeyController {

    private final DonkeyService donkeyService;

    public DonkeyController(DonkeyService donkeyService) {
        this.donkeyService = donkeyService;
    }

    @GetMapping
    public Page<DonkeyResponse> findAll(@PageableDefault(size = 20) Pageable pageable) {
        return donkeyService.findAll(pageable);
    }

    @GetMapping("/{id}")
    public DonkeyResponse findById(@PathVariable Long id) {
        return donkeyService.findById(id);
    }

    @PostMapping
    public ResponseEntity<DonkeyResponse> create(@Valid @RequestBody DonkeyRequest request) {
        DonkeyResponse created = donkeyService.create(request);
        return ResponseEntity.created(URI.create("/api/v1/donkeys/" + created.id())).body(created);
    }

    @PutMapping("/{id}")
    public DonkeyResponse update(@PathVariable Long id, @Valid @RequestBody DonkeyRequest request) {
        return donkeyService.update(id, request);
    }

    @DeleteMapping("/{id}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void delete(@PathVariable Long id) {
        donkeyService.delete(id);
    }
}
