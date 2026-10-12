package com.example.farm.service;

import com.example.farm.dto.HorseRequest;
import com.example.farm.dto.HorseResponse;
import com.example.farm.exception.NotFoundException;
import com.example.farm.model.Horse;
import com.example.farm.repository.HorseRepository;
import java.util.Objects;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/** Business logic for the horses of the farm. */
@Service
public class HorseService {

    private final HorseRepository horseRepository;
    private final StableService stableService;

    public HorseService(HorseRepository horseRepository, StableService stableService) {
        this.horseRepository = horseRepository;
        this.stableService = stableService;
    }

    @Transactional(readOnly = true)
    public Page<HorseResponse> findAll(Pageable pageable) {
        return horseRepository.findAll(pageable).map(this::toResponse);
    }

    @Transactional(readOnly = true)
    public HorseResponse findById(Long id) {
        return toResponse(getHorse(id));
    }

    @Transactional
    public HorseResponse create(HorseRequest request) {
        Horse horse = new Horse();
        apply(horse, request);
        horse.setStable(stableService.getStableWithFreePlace(request.stableId()));
        return toResponse(horseRepository.save(horse));
    }

    @Transactional
    public HorseResponse update(Long id, HorseRequest request) {
        Horse horse = getHorse(id);
        apply(horse, request);
        Long currentStableId = horse.getStable() == null ? null : horse.getStable().getId();
        if (!Objects.equals(currentStableId, request.stableId())) {
            horse.setStable(stableService.getStableWithFreePlace(request.stableId()));
        }
        return toResponse(horseRepository.save(horse));
    }

    @Transactional
    public void delete(Long id) {
        horseRepository.delete(getHorse(id));
    }

    private Horse getHorse(Long id) {
        return horseRepository.findById(id)
                .orElseThrow(() -> new NotFoundException("Horse " + id + " not found"));
    }

    private void apply(Horse horse, HorseRequest request) {
        horse.setName(request.name());
        horse.setBirthDate(request.birthDate());
        horse.setWeightKg(request.weightKg());
        horse.setBreed(request.breed());
        horse.setWithersHeightCm(request.withersHeightCm());
    }

    private HorseResponse toResponse(Horse horse) {
        return new HorseResponse(horse.getId(), horse.getName(), horse.getBirthDate(), horse.getWeightKg(), horse.getBreed(), horse.getWithersHeightCm(), horse.getStable() == null ? null : horse.getStable().getId());
    }
}
