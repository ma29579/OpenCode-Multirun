package com.example.farm.dto;

import java.math.BigDecimal;
import java.time.LocalDate;

public record CowResponse(Long id, String name, LocalDate birthDate, BigDecimal weightKg, String breed, BigDecimal dailyMilkLiters, Long stableId) {
}
