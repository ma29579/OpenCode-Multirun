package com.example.farm.controller;

import com.example.farm.dto.CowRequest;
import com.example.farm.dto.CowResponse;
import com.example.farm.service.CowService;
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
@RequestMapping("/api/v1/cows")
public class CowController {

    private final CowService cowService;

    public CowController(CowService cowService) {
        this.cowService = cowService;
    }

    @GetMapping
    public Page<CowResponse> findAll(@PageableDefault(size = 20) Pageable pageable) {
        return cowService.findAll(pageable);
    }

    @GetMapping("/{id}")
    public CowResponse findById(@PathVariable Long id) {
        return cowService.findById(id);
    }

    @PostMapping
    public ResponseEntity<CowResponse> create(@Valid @RequestBody CowRequest request) {
        CowResponse created = cowService.create(request);
        return ResponseEntity.created(URI.create("/api/v1/cows/" + created.id())).body(created);
    }

    @PutMapping("/{id}")
    public CowResponse update(@PathVariable Long id, @Valid @RequestBody CowRequest request) {
        return cowService.update(id, request);
    }

    @DeleteMapping("/{id}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void delete(@PathVariable Long id) {
        cowService.delete(id);
    }
}
