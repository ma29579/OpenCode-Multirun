package com.example.farm.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.PastOrPresent;
import jakarta.validation.constraints.Positive;
import jakarta.validation.constraints.Size;
import java.math.BigDecimal;
import java.time.LocalDate;

public record CowRequest(
        @NotBlank @Size(max = 100) String name,
        @NotNull @PastOrPresent LocalDate birthDate,
        @NotNull @Positive BigDecimal weightKg,
        @NotBlank @Size(max = 100) String breed,
        @NotNull @Positive BigDecimal dailyMilkLiters,
        Long stableId) {
}
