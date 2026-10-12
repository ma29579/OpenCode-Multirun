package com.example.farm.controller;

import com.example.farm.dto.DonkeyRequest;
import com.example.farm.dto.DonkeyResponse;
import com.example.farm.model.Donkey;

public final class DonkeyMapper {

    private DonkeyMapper() {
    }

    public static void apply(Donkey donkey, DonkeyRequest request) {
        donkey.setName(request.name());
        donkey.setBirthDate(request.birthDate());
        donkey.setWeightKg(request.weightKg());
        donkey.setBreed(request.breed());
        donkey.setMaxLoadKg(request.maxLoadKg());
    }

    public static DonkeyResponse toResponse(Donkey donkey) {
        return new DonkeyResponse(donkey.getId(), donkey.getName(), donkey.getBirthDate(), donkey.getWeightKg(), donkey.getBreed(), donkey.getMaxLoadKg(), donkey.getStable() == null ? null : donkey.getStable().getId());
    }
}
