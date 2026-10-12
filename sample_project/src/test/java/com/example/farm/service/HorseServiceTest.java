package com.example.farm.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.example.farm.dto.HorseRequest;
import com.example.farm.dto.HorseResponse;
import com.example.farm.exception.ConflictException;
import com.example.farm.exception.NotFoundException;
import com.example.farm.model.Horse;
import com.example.farm.model.Stable;
import com.example.farm.repository.HorseRepository;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageImpl;
import org.springframework.data.domain.PageRequest;
import org.springframework.test.util.ReflectionTestUtils;

@ExtendWith(MockitoExtension.class)
@DisplayName("HorseService")
class HorseServiceTest {

    private static final LocalDate BIRTH_DATE = LocalDate.of(2018, 4, 12);

    @Mock
    private HorseRepository horseRepository;

    @Mock
    private StableService stableService;

    private HorseService horseService;

    @BeforeEach
    void setUp() {
        horseService = new HorseService(horseRepository, stableService);
    }

    @Test
    @DisplayName("Returns a page of horse responses mapped from the stored horses")
    void findAllMapsEntitiesToResponses() {
        Horse horse = horse(1L, "Blitz", null);
        when(horseRepository.findAll(PageRequest.of(0, 20))).thenReturn(new PageImpl<>(List.of(horse)));

        Page<HorseResponse> page = horseService.findAll(PageRequest.of(0, 20));

        assertThat(page.getContent()).hasSize(1);
        assertThat(page.getContent().get(0).name()).isEqualTo("Blitz");
        assertThat(page.getContent().get(0).stableId()).isNull();
    }

    @Test
    @DisplayName("Returns the horse with the given id including the id of its stable")
    void findByIdReturnsResponse() {
        when(horseRepository.findById(1L)).thenReturn(Optional.of(horse(1L, "Blitz", stable(7L))));

        HorseResponse response = horseService.findById(1L);

        assertThat(response.id()).isEqualTo(1L);
        assertThat(response.withersHeightCm()).isEqualTo(148);
        assertThat(response.stableId()).isEqualTo(7L);
    }

    @Test
    @DisplayName("Throws NotFoundException when the requested horse does not exist")
    void findByIdThrowsWhenMissing() {
        when(horseRepository.findById(99L)).thenReturn(Optional.empty());

        assertThatThrownBy(() -> horseService.findById(99L))
                .isInstanceOf(NotFoundException.class)
                .hasMessageContaining("99");
    }

    @Test
    @DisplayName("Creates a horse and places it in the stable that has a free place")
    void createAssignsStableWithFreePlace() {
        Stable stable = stable(7L);
        when(stableService.getStableWithFreePlace(7L)).thenReturn(stable);
        when(horseRepository.save(any(Horse.class))).thenAnswer(invocation -> invocation.getArgument(0));

        HorseResponse response = horseService.create(request(7L, 148));

        assertThat(response.name()).isEqualTo("Blitz");
        assertThat(response.stableId()).isEqualTo(7L);
        verify(horseRepository).save(any(Horse.class));
    }

    @Test
    @DisplayName("Creates a horse without a stable when no stable id is given")
    void createWithoutStable() {
        when(horseRepository.save(any(Horse.class))).thenAnswer(invocation -> invocation.getArgument(0));

        HorseResponse response = horseService.create(request(null, 148));

        assertThat(response.stableId()).isNull();
    }

    @Test
    @DisplayName("Does not save the horse when the chosen stable is full")
    void createFailsWhenStableIsFull() {
        when(stableService.getStableWithFreePlace(7L)).thenThrow(new ConflictException("Stable 7 is full"));

        assertThatThrownBy(() -> horseService.create(request(7L, 148)))
                .isInstanceOf(ConflictException.class);

        verify(horseRepository, never()).save(any(Horse.class));
    }

    @Test
    @DisplayName("Updates the horse data without checking the stable when the stable does not change")
    void updateKeepsStable() {
        when(horseRepository.findById(1L)).thenReturn(Optional.of(horse(1L, "Blitz", stable(7L))));
        when(horseRepository.save(any(Horse.class))).thenAnswer(invocation -> invocation.getArgument(0));

        HorseResponse response = horseService.update(1L, request(7L, 150));

        assertThat(response.withersHeightCm()).isEqualTo(150);
        verify(stableService, never()).getStableWithFreePlace(any());
    }

    @Test
    @DisplayName("Moves the horse to the new stable after checking that it has a free place")
    void updateMovesToNewStable() {
        when(horseRepository.findById(1L)).thenReturn(Optional.of(horse(1L, "Blitz", stable(7L))));
        when(stableService.getStableWithFreePlace(8L)).thenReturn(stable(8L));
        when(horseRepository.save(any(Horse.class))).thenAnswer(invocation -> invocation.getArgument(0));

        HorseResponse response = horseService.update(1L, request(8L, 148));

        assertThat(response.stableId()).isEqualTo(8L);
    }

    @Test
    @DisplayName("Throws NotFoundException when updating a horse that does not exist")
    void updateThrowsWhenMissing() {
        when(horseRepository.findById(99L)).thenReturn(Optional.empty());

        assertThatThrownBy(() -> horseService.update(99L, request(null, 148)))
                .isInstanceOf(NotFoundException.class);
    }

    @Test
    @DisplayName("Deletes an existing horse")
    void deleteRemovesEntity() {
        Horse horse = horse(1L, "Blitz", null);
        when(horseRepository.findById(1L)).thenReturn(Optional.of(horse));

        horseService.delete(1L);

        verify(horseRepository).delete(horse);
    }

    @Test
    @DisplayName("Throws NotFoundException when deleting a horse that does not exist")
    void deleteThrowsWhenMissing() {
        when(horseRepository.findById(99L)).thenReturn(Optional.empty());

        assertThatThrownBy(() -> horseService.delete(99L)).isInstanceOf(NotFoundException.class);

        verify(horseRepository, never()).delete(any(Horse.class));
    }

    private HorseRequest request(Long stableId, Integer withersHeightCm) {
        return new HorseRequest("Blitz", BIRTH_DATE, new BigDecimal("520.50"), "Haflinger", withersHeightCm, stableId);
    }

    private Horse horse(Long id, String name, Stable stable) {
        Horse horse = new Horse();
        ReflectionTestUtils.setField(horse, "id", id);
        horse.setName(name);
        horse.setBirthDate(BIRTH_DATE);
        horse.setWeightKg(new BigDecimal("520.50"));
        horse.setBreed("Haflinger");
        horse.setWithersHeightCm(148);
        horse.setStable(stable);
        return horse;
    }

    private Stable stable(Long id) {
        Stable stable = new Stable();
        ReflectionTestUtils.setField(stable, "id", id);
        return stable;
    }
}
