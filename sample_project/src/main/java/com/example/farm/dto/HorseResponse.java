package com.example.farm.dto;

import java.math.BigDecimal;
import java.time.LocalDate;

public record HorseResponse(Long id, String name, LocalDate birthDate, BigDecimal weightKg, String breed, Integer withersHeightCm, Long stableId) {
}
