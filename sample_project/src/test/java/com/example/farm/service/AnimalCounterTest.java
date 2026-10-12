package com.example.farm.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.Mockito.when;

import com.example.farm.model.Stable;
import com.example.farm.repository.CowRepository;
import com.example.farm.repository.DonkeyRepository;
import com.example.farm.repository.GoatRepository;
import com.example.farm.repository.HorseRepository;
import com.example.farm.repository.PigRepository;
import com.example.farm.repository.RabbitRepository;
import com.example.farm.repository.SheepRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.test.util.ReflectionTestUtils;

@ExtendWith(MockitoExtension.class)
@DisplayName("AnimalCounter")
class AnimalCounterTest {

    @Mock
    private HorseRepository horseRepository;
    @Mock
    private CowRepository cowRepository;
    @Mock
    private DonkeyRepository donkeyRepository;
    @Mock
    private PigRepository pigRepository;
    @Mock
    private GoatRepository goatRepository;
    @Mock
    private SheepRepository sheepRepository;
    @Mock
    private RabbitRepository rabbitRepository;

    private AnimalCounter animalCounter;

    @BeforeEach
    void setUp() {
        animalCounter = new AnimalCounter(horseRepository, cowRepository, donkeyRepository, pigRepository,
                goatRepository, sheepRepository, rabbitRepository);
    }

    @Test
    @DisplayName("Adds up the animals of all seven species that live in the stable")
    void countsAllSpecies() {
        Stable stable = stable(1L, "Main barn");
        when(horseRepository.countByStableId(1L)).thenReturn(1L);
        when(cowRepository.countByStableId(1L)).thenReturn(2L);
        when(donkeyRepository.countByStableId(1L)).thenReturn(3L);
        when(pigRepository.countByStableId(1L)).thenReturn(4L);
        when(goatRepository.countByStableId(1L)).thenReturn(5L);
        when(sheepRepository.countByStableName("Main barn")).thenReturn(6L);
        when(rabbitRepository.countByStableId(1L)).thenReturn(7L);

        assertThat(animalCounter.countInStable(stable)).isEqualTo(28L);
    }

    @Test
    @DisplayName("Returns zero for an empty stable")
    void countsZeroForEmptyStable() {
        Stable stable = stable(2L, "Empty barn");

        assertThat(animalCounter.countInStable(stable)).isZero();
    }

    private Stable stable(Long id, String name) {
        Stable stable = new Stable();
        ReflectionTestUtils.setField(stable, "id", id);
        stable.setName(name);
        return stable;
    }
}
