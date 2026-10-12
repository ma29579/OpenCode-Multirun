package com.example.farm.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.Mockito.when;

import com.example.farm.model.Pig;
import com.example.farm.repository.PigRepository;
import java.util.List;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

@ExtendWith(MockitoExtension.class)
@DisplayName("PigService")
class PigServiceTest {

    @Mock
    private PigRepository pigRepository;

    @InjectMocks
    private PigService pigService;

    @Test
    @DisplayName("Returns all pigs from the repository")
    void findAllReturnsAllPigs() {
        when(pigRepository.findAll()).thenReturn(List.of(new Pig(), new Pig()));

        assertThat(pigService.findAll()).hasSize(2);
    }

    @Test
    @DisplayName("Calculates 100 fattening days for a target weight of 100 kg")
    void fatteningDaysForTargetWeight() {
        assertThat(pigService.fatteningDays(pig(100.0))).isEqualTo(100);
    }

    @Test
    @DisplayName("Rounds the number of fattening days up to the next full day")
    void fatteningDaysRoundsUp() {
        assertThat(pigService.fatteningDays(pig(30.0))).isEqualTo(7);
    }

    @Test
    @DisplayName("Needs no fattening days for a target weight of 25 kg")
    void fatteningDaysIsZeroAtStartWeight() {
        assertThat(pigService.fatteningDays(pig(25.0))).isZero();
    }

    private Pig pig(double targetWeightKg) {
        Pig pig = new Pig();
        pig.setTargetWeightKg(targetWeightKg);
        return pig;
    }
}
