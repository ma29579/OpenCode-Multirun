package com.example.farm.service;

import com.example.farm.dto.CowRequest;
import com.example.farm.dto.CowResponse;
import com.example.farm.exception.NotFoundException;
import com.example.farm.model.Cow;
import com.example.farm.repository.CowRepository;
import java.util.Objects;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/** Business logic for the cows of the farm. */
@Service
public class CowService {

    private final CowRepository cowRepository;
    private final StableService stableService;

    public CowService(CowRepository cowRepository, StableService stableService) {
        this.cowRepository = cowRepository;
        this.stableService = stableService;
    }

    @Transactional(readOnly = true)
    public Page<CowResponse> findAll(Pageable pageable) {
        return cowRepository.findAll(pageable).map(this::toResponse);
    }

    @Transactional(readOnly = true)
    public CowResponse findById(Long id) {
        return toResponse(getCow(id));
    }

    @Transactional
    public CowResponse create(CowRequest request) {
        Cow cow = new Cow();
        apply(cow, request);
        cow.setStable(stableService.getStableWithFreePlace(request.stableId()));
        return toResponse(cowRepository.save(cow));
    }

    @Transactional
    public CowResponse update(Long id, CowRequest request) {
        Cow cow = getCow(id);
        apply(cow, request);
        Long currentStableId = cow.getStable() == null ? null : cow.getStable().getId();
        if (!Objects.equals(currentStableId, request.stableId())) {
            cow.setStable(stableService.getStableWithFreePlace(request.stableId()));
        }
        return toResponse(cowRepository.save(cow));
    }

    @Transactional
    public void delete(Long id) {
        cowRepository.delete(getCow(id));
    }

    private Cow getCow(Long id) {
        return cowRepository.findById(id)
                .orElseThrow(() -> new NotFoundException("Cow " + id + " not found"));
    }

    private void apply(Cow cow, CowRequest request) {
        cow.setName(request.name());
        cow.setBirthDate(request.birthDate());
        cow.setWeightKg(request.weightKg());
        cow.setBreed(request.breed());
        cow.setDailyMilkLiters(request.dailyMilkLiters());
    }

    private CowResponse toResponse(Cow cow) {
        return new CowResponse(cow.getId(), cow.getName(), cow.getBirthDate(), cow.getWeightKg(), cow.getBreed(), cow.getDailyMilkLiters(), cow.getStable() == null ? null : cow.getStable().getId());
    }
}
