package com.example.farm.dto;

import com.example.farm.model.StableType;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Positive;
import jakarta.validation.constraints.Size;

public record StableRequest(
        @NotBlank @Size(max = 100) String name,
        @NotNull @Positive Integer capacity,
        @NotNull StableType type) {
}
