package com.example.farm.service;

import com.example.farm.controller.DonkeyMapper;
import com.example.farm.dto.DonkeyRequest;
import com.example.farm.dto.DonkeyResponse;
import com.example.farm.exception.NotFoundException;
import com.example.farm.model.Donkey;
import com.example.farm.repository.DonkeyRepository;
import java.util.Objects;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/** Business logic for the donkeys of the farm. */
@Service
public class DonkeyService {

    private final DonkeyRepository donkeyRepository;
    private final StableService stableService;

    public DonkeyService(DonkeyRepository donkeyRepository, StableService stableService) {
        this.donkeyRepository = donkeyRepository;
        this.stableService = stableService;
    }

    @Transactional(readOnly = true)
    public Page<DonkeyResponse> findAll(Pageable pageable) {
        return donkeyRepository.findAll(pageable).map(DonkeyMapper::toResponse);
    }

    @Transactional(readOnly = true)
    public DonkeyResponse findById(Long id) {
        return DonkeyMapper.toResponse(getDonkey(id));
    }

    @Transactional
    public DonkeyResponse create(DonkeyRequest request) {
        Donkey donkey = new Donkey();
        DonkeyMapper.apply(donkey, request);
        donkey.setStable(stableService.getStableWithFreePlace(request.stableId()));
        return DonkeyMapper.toResponse(donkeyRepository.save(donkey));
    }

    @Transactional
    public DonkeyResponse update(Long id, DonkeyRequest request) {
        Donkey donkey = getDonkey(id);
        DonkeyMapper.apply(donkey, request);
        Long currentStableId = donkey.getStable() == null ? null : donkey.getStable().getId();
        if (!Objects.equals(currentStableId, request.stableId())) {
            donkey.setStable(stableService.getStableWithFreePlace(request.stableId()));
        }
        return DonkeyMapper.toResponse(donkeyRepository.save(donkey));
    }

    @Transactional
    public void delete(Long id) {
        donkeyRepository.delete(getDonkey(id));
    }

    private Donkey getDonkey(Long id) {
        return donkeyRepository.findById(id)
                .orElseThrow(() -> new NotFoundException("Donkey " + id + " not found"));
    }
}
