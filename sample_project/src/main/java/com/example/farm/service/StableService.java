package com.example.farm.service;

import com.example.farm.dto.StableRequest;
import com.example.farm.dto.StableResponse;
import com.example.farm.exception.ConflictException;
import com.example.farm.exception.NotFoundException;
import com.example.farm.model.Stable;
import com.example.farm.repository.StableRepository;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/** Business logic for the stables of the farm, including the capacity rules. */
@Service
public class StableService {

    private final StableRepository stableRepository;
    private final AnimalCounter animalCounter;

    public StableService(StableRepository stableRepository, AnimalCounter animalCounter) {
        this.stableRepository = stableRepository;
        this.animalCounter = animalCounter;
    }

    @Transactional(readOnly = true)
    public Page<StableResponse> findAll(Pageable pageable) {
        return stableRepository.findAll(pageable).map(this::toResponse);
    }

    @Transactional(readOnly = true)
    public StableResponse findById(Long id) {
        return toResponse(getStable(id));
    }

    @Transactional
    public StableResponse create(StableRequest request) {
        Stable stable = new Stable();
        apply(stable, request);
        return toResponse(stableRepository.save(stable));
    }

    @Transactional
    public StableResponse update(Long id, StableRequest request) {
        Stable stable = getStable(id);
        if (request.capacity() < animalCounter.countInStable(stable)) {
            throw new ConflictException("Capacity is smaller than the number of animals in stable " + id);
        }
        apply(stable, request);
        return toResponse(stableRepository.save(stable));
    }

    @Transactional
    public void delete(Long id) {
        Stable stable = getStable(id);
        if (animalCounter.countInStable(stable) > 0) {
            throw new ConflictException("Stable " + id + " still contains animals");
        }
        stableRepository.delete(stable);
    }

    /**
     * Returns the stable with the given id after checking that it has a free place.
     *
     * @param stableId id of the stable, may be {@code null} for an animal without stable
     * @return the stable, or {@code null} if no id was given
     */
    @Transactional(readOnly = true)
    public Stable getStableWithFreePlace(Long stableId) {
        if (stableId == null) {
            return null;
        }
        Stable stable = getStable(stableId);
        if (animalCounter.countInStable(stable) >= stable.getCapacity()) {
            throw new ConflictException("Stable " + stableId + " is full");
        }
        return stable;
    }

    private Stable getStable(Long id) {
        return stableRepository.findById(id)
                .orElseThrow(() -> new NotFoundException("Stable " + id + " not found"));
    }

    private void apply(Stable stable, StableRequest request) {
        stable.setName(request.name());
        stable.setCapacity(request.capacity());
        stable.setType(request.type());
    }

    private StableResponse toResponse(Stable stable) {
        return new StableResponse(stable.getId(), stable.getName(), stable.getCapacity(), stable.getType(),
                animalCounter.countInStable(stable));
    }
}
