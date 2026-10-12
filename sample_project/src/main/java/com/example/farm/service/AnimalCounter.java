package com.example.farm.service;

import com.example.farm.model.Stable;
import com.example.farm.repository.CowRepository;
import com.example.farm.repository.DonkeyRepository;
import com.example.farm.repository.GoatRepository;
import com.example.farm.repository.HorseRepository;
import com.example.farm.repository.PigRepository;
import com.example.farm.repository.RabbitRepository;
import com.example.farm.repository.SheepRepository;
import org.springframework.stereotype.Component;

/** Counts the animals of all species that live in a stable. */
@Component
public class AnimalCounter {

    private final HorseRepository horseRepository;
    private final CowRepository cowRepository;
    private final DonkeyRepository donkeyRepository;
    private final PigRepository pigRepository;
    private final GoatRepository goatRepository;
    private final SheepRepository sheepRepository;
    private final RabbitRepository rabbitRepository;

    public AnimalCounter(HorseRepository horseRepository, CowRepository cowRepository,
            DonkeyRepository donkeyRepository, PigRepository pigRepository, GoatRepository goatRepository,
            SheepRepository sheepRepository, RabbitRepository rabbitRepository) {
        this.horseRepository = horseRepository;
        this.cowRepository = cowRepository;
        this.donkeyRepository = donkeyRepository;
        this.pigRepository = pigRepository;
        this.goatRepository = goatRepository;
        this.sheepRepository = sheepRepository;
        this.rabbitRepository = rabbitRepository;
    }

    public long countInStable(Stable stable) {
        Long stableId = stable.getId();
        return horseRepository.countByStableId(stableId)
                + cowRepository.countByStableId(stableId)
                + donkeyRepository.countByStableId(stableId)
                + pigRepository.countByStableId(stableId)
                + goatRepository.countByStableId(stableId)
                + sheepRepository.countByStableName(stable.getName())
                + rabbitRepository.countByStableId(stableId);
    }
}
