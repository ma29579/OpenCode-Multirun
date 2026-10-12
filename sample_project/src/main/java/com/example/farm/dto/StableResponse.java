package com.example.farm.dto;

import com.example.farm.model.StableType;

public record StableResponse(Long id, String name, int capacity, StableType type, long occupiedPlaces) {
}
