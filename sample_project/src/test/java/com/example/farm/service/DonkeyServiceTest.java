package com.example.farm.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.example.farm.dto.DonkeyRequest;
import com.example.farm.dto.DonkeyResponse;
import com.example.farm.exception.ConflictException;
import com.example.farm.exception.NotFoundException;
import com.example.farm.model.Donkey;
import com.example.farm.model.Stable;
import com.example.farm.repository.DonkeyRepository;
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
@DisplayName("DonkeyService")
class DonkeyServiceTest {

    private static final LocalDate BIRTH_DATE = LocalDate.of(2018, 4, 12);

    @Mock
    private DonkeyRepository donkeyRepository;

    @Mock
    private StableService stableService;

    private DonkeyService donkeyService;

    @BeforeEach
    void setUp() {
        donkeyService = new DonkeyService(donkeyRepository, stableService);
    }

    @Test
    @DisplayName("Returns a page of donkey responses mapped from the stored donkeys")
    void findAllMapsEntitiesToResponses() {
        Donkey donkey = donkey(1L, "Blitz", null);
        when(donkeyRepository.findAll(PageRequest.of(0, 20))).thenReturn(new PageImpl<>(List.of(donkey)));

        Page<DonkeyResponse> page = donkeyService.findAll(PageRequest.of(0, 20));

        assertThat(page.getContent()).hasSize(1);
        assertThat(page.getContent().get(0).name()).isEqualTo("Blitz");
        assertThat(page.getContent().get(0).stableId()).isNull();
    }

    @Test
    @DisplayName("Returns the donkey with the given id including the id of its stable")
    void findByIdReturnsResponse() {
        when(donkeyRepository.findById(1L)).thenReturn(Optional.of(donkey(1L, "Blitz", stable(7L))));

        DonkeyResponse response = donkeyService.findById(1L);

        assertThat(response.id()).isEqualTo(1L);
        assertThat(response.maxLoadKg()).isEqualTo(new BigDecimal("60.00"));
        assertThat(response.stableId()).isEqualTo(7L);
    }

    @Test
    @DisplayName("Throws NotFoundException when the requested donkey does not exist")
    void findByIdThrowsWhenMissing() {
        when(donkeyRepository.findById(99L)).thenReturn(Optional.empty());

        assertThatThrownBy(() -> donkeyService.findById(99L))
                .isInstanceOf(NotFoundException.class)
                .hasMessageContaining("99");
    }

    @Test
    @DisplayName("Creates a donkey and places it in the stable that has a free place")
    void createAssignsStableWithFreePlace() {
        Stable stable = stable(7L);
        when(stableService.getStableWithFreePlace(7L)).thenReturn(stable);
        when(donkeyRepository.save(any(Donkey.class))).thenAnswer(invocation -> invocation.getArgument(0));

        DonkeyResponse response = donkeyService.create(request(7L, new BigDecimal("60.00")));

        assertThat(response.name()).isEqualTo("Blitz");
        assertThat(response.stableId()).isEqualTo(7L);
        verify(donkeyRepository).save(any(Donkey.class));
    }

    @Test
    @DisplayName("Creates a donkey without a stable when no stable id is given")
    void createWithoutStable() {
        when(donkeyRepository.save(any(Donkey.class))).thenAnswer(invocation -> invocation.getArgument(0));

        DonkeyResponse response = donkeyService.create(request(null, new BigDecimal("60.00")));

        assertThat(response.stableId()).isNull();
    }

    @Test
    @DisplayName("Does not save the donkey when the chosen stable is full")
    void createFailsWhenStableIsFull() {
        when(stableService.getStableWithFreePlace(7L)).thenThrow(new ConflictException("Stable 7 is full"));

        assertThatThrownBy(() -> donkeyService.create(request(7L, new BigDecimal("60.00"))))
                .isInstanceOf(ConflictException.class);

        verify(donkeyRepository, never()).save(any(Donkey.class));
    }

    @Test
    @DisplayName("Updates the donkey data without checking the stable when the stable does not change")
    void updateKeepsStable() {
        when(donkeyRepository.findById(1L)).thenReturn(Optional.of(donkey(1L, "Blitz", stable(7L))));
        when(donkeyRepository.save(any(Donkey.class))).thenAnswer(invocation -> invocation.getArgument(0));

        DonkeyResponse response = donkeyService.update(1L, request(7L, new BigDecimal("65.00")));

        assertThat(response.maxLoadKg()).isEqualTo(new BigDecimal("65.00"));
        verify(stableService, never()).getStableWithFreePlace(any());
    }

    @Test
    @DisplayName("Moves the donkey to the new stable after checking that it has a free place")
    void updateMovesToNewStable() {
        when(donkeyRepository.findById(1L)).thenReturn(Optional.of(donkey(1L, "Blitz", stable(7L))));
        when(stableService.getStableWithFreePlace(8L)).thenReturn(stable(8L));
        when(donkeyRepository.save(any(Donkey.class))).thenAnswer(invocation -> invocation.getArgument(0));

        DonkeyResponse response = donkeyService.update(1L, request(8L, new BigDecimal("60.00")));

        assertThat(response.stableId()).isEqualTo(8L);
    }

    @Test
    @DisplayName("Throws NotFoundException when updating a donkey that does not exist")
    void updateThrowsWhenMissing() {
        when(donkeyRepository.findById(99L)).thenReturn(Optional.empty());

        assertThatThrownBy(() -> donkeyService.update(99L, request(null, new BigDecimal("60.00"))))
                .isInstanceOf(NotFoundException.class);
    }

    @Test
    @DisplayName("Deletes an existing donkey")
    void deleteRemovesEntity() {
        Donkey donkey = donkey(1L, "Blitz", null);
        when(donkeyRepository.findById(1L)).thenReturn(Optional.of(donkey));

        donkeyService.delete(1L);

        verify(donkeyRepository).delete(donkey);
    }

    @Test
    @DisplayName("Throws NotFoundException when deleting a donkey that does not exist")
    void deleteThrowsWhenMissing() {
        when(donkeyRepository.findById(99L)).thenReturn(Optional.empty());

        assertThatThrownBy(() -> donkeyService.delete(99L)).isInstanceOf(NotFoundException.class);

        verify(donkeyRepository, never()).delete(any(Donkey.class));
    }

    private DonkeyRequest request(Long stableId, BigDecimal maxLoadKg) {
        return new DonkeyRequest("Blitz", BIRTH_DATE, new BigDecimal("520.50"), "Haflinger", maxLoadKg, stableId);
    }

    private Donkey donkey(Long id, String name, Stable stable) {
        Donkey donkey = new Donkey();
        ReflectionTestUtils.setField(donkey, "id", id);
        donkey.setName(name);
        donkey.setBirthDate(BIRTH_DATE);
        donkey.setWeightKg(new BigDecimal("520.50"));
        donkey.setBreed("Haflinger");
        donkey.setMaxLoadKg(new BigDecimal("60.00"));
        donkey.setStable(stable);
        return donkey;
    }

    private Stable stable(Long id) {
        Stable stable = new Stable();
        ReflectionTestUtils.setField(stable, "id", id);
        return stable;
    }
}
