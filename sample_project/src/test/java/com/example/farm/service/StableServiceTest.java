package com.example.farm.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.example.farm.dto.StableRequest;
import com.example.farm.dto.StableResponse;
import com.example.farm.exception.ConflictException;
import com.example.farm.exception.NotFoundException;
import com.example.farm.model.Stable;
import com.example.farm.model.StableType;
import com.example.farm.repository.StableRepository;
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
@DisplayName("StableService")
class StableServiceTest {

    @Mock
    private StableRepository stableRepository;

    @Mock
    private AnimalCounter animalCounter;

    private StableService stableService;

    @BeforeEach
    void setUp() {
        stableService = new StableService(stableRepository, animalCounter);
    }

    @Test
    @DisplayName("Returns stables together with the number of occupied places")
    void findAllIncludesOccupiedPlaces() {
        Stable stable = stable(1L, "Main barn", 5);
        when(stableRepository.findAll(PageRequest.of(0, 20))).thenReturn(new PageImpl<>(List.of(stable)));
        when(animalCounter.countInStable(stable)).thenReturn(3L);

        Page<StableResponse> page = stableService.findAll(PageRequest.of(0, 20));

        assertThat(page.getContent()).hasSize(1);
        assertThat(page.getContent().get(0).occupiedPlaces()).isEqualTo(3L);
        assertThat(page.getContent().get(0).capacity()).isEqualTo(5);
    }

    @Test
    @DisplayName("Throws NotFoundException when the stable does not exist")
    void findByIdThrowsWhenMissing() {
        when(stableRepository.findById(99L)).thenReturn(Optional.empty());

        assertThatThrownBy(() -> stableService.findById(99L)).isInstanceOf(NotFoundException.class);
    }

    @Test
    @DisplayName("Creates a stable from the request data")
    void createSavesStable() {
        when(stableRepository.save(any(Stable.class))).thenAnswer(invocation -> invocation.getArgument(0));

        StableResponse response = stableService.create(new StableRequest("Cowshed", 10, StableType.COWSHED));

        assertThat(response.name()).isEqualTo("Cowshed");
        assertThat(response.type()).isEqualTo(StableType.COWSHED);
        assertThat(response.capacity()).isEqualTo(10);
    }

    @Test
    @DisplayName("Rejects a capacity that is smaller than the number of animals in the stable")
    void updateRejectsTooSmallCapacity() {
        Stable stable = stable(1L, "Main barn", 5);
        when(stableRepository.findById(1L)).thenReturn(Optional.of(stable));
        when(animalCounter.countInStable(stable)).thenReturn(4L);

        assertThatThrownBy(() -> stableService.update(1L, new StableRequest("Main barn", 3, StableType.MIXED)))
                .isInstanceOf(ConflictException.class);

        verify(stableRepository, never()).save(any(Stable.class));
    }

    @Test
    @DisplayName("Updates name, capacity and type of the stable")
    void updateAppliesChanges() {
        Stable stable = stable(1L, "Main barn", 5);
        when(stableRepository.findById(1L)).thenReturn(Optional.of(stable));
        when(animalCounter.countInStable(stable)).thenReturn(2L);
        when(stableRepository.save(stable)).thenReturn(stable);

        StableResponse response = stableService.update(1L, new StableRequest("Big barn", 8, StableType.MIXED));

        assertThat(response.name()).isEqualTo("Big barn");
        assertThat(response.capacity()).isEqualTo(8);
        assertThat(response.type()).isEqualTo(StableType.MIXED);
    }

    @Test
    @DisplayName("Refuses to delete a stable that still contains animals")
    void deleteRejectsOccupiedStable() {
        Stable stable = stable(1L, "Main barn", 5);
        when(stableRepository.findById(1L)).thenReturn(Optional.of(stable));
        when(animalCounter.countInStable(stable)).thenReturn(1L);

        assertThatThrownBy(() -> stableService.delete(1L)).isInstanceOf(ConflictException.class);

        verify(stableRepository, never()).delete(any(Stable.class));
    }

    @Test
    @DisplayName("Deletes an empty stable")
    void deleteRemovesEmptyStable() {
        Stable stable = stable(1L, "Main barn", 5);
        when(stableRepository.findById(1L)).thenReturn(Optional.of(stable));
        when(animalCounter.countInStable(stable)).thenReturn(0L);

        stableService.delete(1L);

        verify(stableRepository).delete(stable);
    }

    @Test
    @DisplayName("Returns no stable when no stable id is given")
    void getStableWithFreePlaceReturnsNullWithoutId() {
        assertThat(stableService.getStableWithFreePlace(null)).isNull();

        verify(stableRepository, never()).findById(any());
    }

    @Test
    @DisplayName("Returns the stable when it still has a free place")
    void getStableWithFreePlaceReturnsStable() {
        Stable stable = stable(1L, "Main barn", 5);
        when(stableRepository.findById(1L)).thenReturn(Optional.of(stable));
        when(animalCounter.countInStable(stable)).thenReturn(4L);

        assertThat(stableService.getStableWithFreePlace(1L)).isSameAs(stable);
    }

    @Test
    @DisplayName("Throws ConflictException when the stable is full")
    void getStableWithFreePlaceRejectsFullStable() {
        Stable stable = stable(1L, "Main barn", 5);
        when(stableRepository.findById(1L)).thenReturn(Optional.of(stable));
        when(animalCounter.countInStable(stable)).thenReturn(5L);

        assertThatThrownBy(() -> stableService.getStableWithFreePlace(1L))
                .isInstanceOf(ConflictException.class)
                .hasMessageContaining("full");
    }

    @Test
    @DisplayName("Throws NotFoundException when the stable for a placement does not exist")
    void getStableWithFreePlaceThrowsWhenMissing() {
        when(stableRepository.findById(99L)).thenReturn(Optional.empty());

        assertThatThrownBy(() -> stableService.getStableWithFreePlace(99L))
                .isInstanceOf(NotFoundException.class);
    }

    private Stable stable(Long id, String name, int capacity) {
        Stable stable = new Stable();
        ReflectionTestUtils.setField(stable, "id", id);
        stable.setName(name);
        stable.setCapacity(capacity);
        stable.setType(StableType.MIXED);
        return stable;
    }
}
