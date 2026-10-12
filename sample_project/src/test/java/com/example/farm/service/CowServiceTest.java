package com.example.farm.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.example.farm.dto.CowRequest;
import com.example.farm.dto.CowResponse;
import com.example.farm.exception.ConflictException;
import com.example.farm.exception.NotFoundException;
import com.example.farm.model.Cow;
import com.example.farm.model.Stable;
import com.example.farm.repository.CowRepository;
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
@DisplayName("CowService")
class CowServiceTest {

    private static final LocalDate BIRTH_DATE = LocalDate.of(2018, 4, 12);

    @Mock
    private CowRepository cowRepository;

    @Mock
    private StableService stableService;

    private CowService cowService;

    @BeforeEach
    void setUp() {
        cowService = new CowService(cowRepository, stableService);
    }

    @Test
    @DisplayName("Returns a page of cow responses mapped from the stored cows")
    void findAllMapsEntitiesToResponses() {
        Cow cow = cow(1L, "Blitz", null);
        when(cowRepository.findAll(PageRequest.of(0, 20))).thenReturn(new PageImpl<>(List.of(cow)));

        Page<CowResponse> page = cowService.findAll(PageRequest.of(0, 20));

        assertThat(page.getContent()).hasSize(1);
        assertThat(page.getContent().get(0).name()).isEqualTo("Blitz");
        assertThat(page.getContent().get(0).stableId()).isNull();
    }

    @Test
    @DisplayName("Returns the cow with the given id including the id of its stable")
    void findByIdReturnsResponse() {
        when(cowRepository.findById(1L)).thenReturn(Optional.of(cow(1L, "Blitz", stable(7L))));

        CowResponse response = cowService.findById(1L);

        assertThat(response.id()).isEqualTo(1L);
        assertThat(response.dailyMilkLiters()).isEqualTo(new BigDecimal("22.50"));
        assertThat(response.stableId()).isEqualTo(7L);
    }

    @Test
    @DisplayName("Throws NotFoundException when the requested cow does not exist")
    void findByIdThrowsWhenMissing() {
        when(cowRepository.findById(99L)).thenReturn(Optional.empty());

        assertThatThrownBy(() -> cowService.findById(99L))
                .isInstanceOf(NotFoundException.class)
                .hasMessageContaining("99");
    }

    @Test
    @DisplayName("Creates a cow and places it in the stable that has a free place")
    void createAssignsStableWithFreePlace() {
        Stable stable = stable(7L);
        when(stableService.getStableWithFreePlace(7L)).thenReturn(stable);
        when(cowRepository.save(any(Cow.class))).thenAnswer(invocation -> invocation.getArgument(0));

        CowResponse response = cowService.create(request(7L, new BigDecimal("22.50")));

        assertThat(response.name()).isEqualTo("Blitz");
        assertThat(response.stableId()).isEqualTo(7L);
        verify(cowRepository).save(any(Cow.class));
    }

    @Test
    @DisplayName("Creates a cow without a stable when no stable id is given")
    void createWithoutStable() {
        when(cowRepository.save(any(Cow.class))).thenAnswer(invocation -> invocation.getArgument(0));

        CowResponse response = cowService.create(request(null, new BigDecimal("22.50")));

        assertThat(response.stableId()).isNull();
    }

    @Test
    @DisplayName("Does not save the cow when the chosen stable is full")
    void createFailsWhenStableIsFull() {
        when(stableService.getStableWithFreePlace(7L)).thenThrow(new ConflictException("Stable 7 is full"));

        assertThatThrownBy(() -> cowService.create(request(7L, new BigDecimal("22.50"))))
                .isInstanceOf(ConflictException.class);

        verify(cowRepository, never()).save(any(Cow.class));
    }

    @Test
    @DisplayName("Updates the cow data without checking the stable when the stable does not change")
    void updateKeepsStable() {
        when(cowRepository.findById(1L)).thenReturn(Optional.of(cow(1L, "Blitz", stable(7L))));
        when(cowRepository.save(any(Cow.class))).thenAnswer(invocation -> invocation.getArgument(0));

        CowResponse response = cowService.update(1L, request(7L, new BigDecimal("25.00")));

        assertThat(response.dailyMilkLiters()).isEqualTo(new BigDecimal("25.00"));
        verify(stableService, never()).getStableWithFreePlace(any());
    }

    @Test
    @DisplayName("Moves the cow to the new stable after checking that it has a free place")
    void updateMovesToNewStable() {
        when(cowRepository.findById(1L)).thenReturn(Optional.of(cow(1L, "Blitz", stable(7L))));
        when(stableService.getStableWithFreePlace(8L)).thenReturn(stable(8L));
        when(cowRepository.save(any(Cow.class))).thenAnswer(invocation -> invocation.getArgument(0));

        CowResponse response = cowService.update(1L, request(8L, new BigDecimal("22.50")));

        assertThat(response.stableId()).isEqualTo(8L);
    }

    @Test
    @DisplayName("Throws NotFoundException when updating a cow that does not exist")
    void updateThrowsWhenMissing() {
        when(cowRepository.findById(99L)).thenReturn(Optional.empty());

        assertThatThrownBy(() -> cowService.update(99L, request(null, new BigDecimal("22.50"))))
                .isInstanceOf(NotFoundException.class);
    }

    @Test
    @DisplayName("Deletes an existing cow")
    void deleteRemovesEntity() {
        Cow cow = cow(1L, "Blitz", null);
        when(cowRepository.findById(1L)).thenReturn(Optional.of(cow));

        cowService.delete(1L);

        verify(cowRepository).delete(cow);
    }

    @Test
    @DisplayName("Throws NotFoundException when deleting a cow that does not exist")
    void deleteThrowsWhenMissing() {
        when(cowRepository.findById(99L)).thenReturn(Optional.empty());

        assertThatThrownBy(() -> cowService.delete(99L)).isInstanceOf(NotFoundException.class);

        verify(cowRepository, never()).delete(any(Cow.class));
    }

    private CowRequest request(Long stableId, BigDecimal dailyMilkLiters) {
        return new CowRequest("Blitz", BIRTH_DATE, new BigDecimal("520.50"), "Haflinger", dailyMilkLiters, stableId);
    }

    private Cow cow(Long id, String name, Stable stable) {
        Cow cow = new Cow();
        ReflectionTestUtils.setField(cow, "id", id);
        cow.setName(name);
        cow.setBirthDate(BIRTH_DATE);
        cow.setWeightKg(new BigDecimal("520.50"));
        cow.setBreed("Haflinger");
        cow.setDailyMilkLiters(new BigDecimal("22.50"));
        cow.setStable(stable);
        return cow;
    }

    private Stable stable(Long id) {
        Stable stable = new Stable();
        ReflectionTestUtils.setField(stable, "id", id);
        return stable;
    }
}
