package com.example.farm.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.example.farm.model.Goat;
import com.example.farm.repository.GoatRepository;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

@ExtendWith(MockitoExtension.class)
@DisplayName("GoatService")
class GoatServiceTest {

    @Mock
    private GoatRepository goatRepository;

    @InjectMocks
    private GoatService goatService;

    @Test
    @DisplayName("Returns all goats from the repository")
    void getAllReturnsAllGoats() {
        when(goatRepository.findAll()).thenReturn(List.of(goat("Heidi", 1L), goat("Gerti", 1L)));

        assertThat(goatService.getAll()).hasSize(2);
    }

    @Test
    @DisplayName("Returns the goat with the given id")
    void getByIdReturnsGoat() {
        Goat goat = goat("Heidi", 1L);
        when(goatRepository.findById(5L)).thenReturn(Optional.of(goat));

        assertThat(goatService.getById(5L)).isSameAs(goat);
    }

    @Test
    @DisplayName("Returns null when the goat does not exist (current behavior)")
    void getByIdReturnsNullWhenMissing() {
        when(goatRepository.findById(99L)).thenReturn(Optional.empty());

        assertThat(goatService.getById(99L)).isNull();
    }

    @Test
    @DisplayName("Saves a goat when its stable has fewer than eight goats")
    void saveStoresGoatWhenStableHasRoom() {
        Goat goat = goat("Heidi", 1L);
        when(goatRepository.countByStableId(1L)).thenReturn(7L);
        when(goatRepository.save(goat)).thenReturn(goat);

        assertThat(goatService.save(goat)).isSameAs(goat);
    }

    @Test
    @DisplayName("Rejects a goat when its stable already holds eight goats")
    void saveRejectsGoatWhenStableIsFull() {
        Goat goat = goat("Heidi", 1L);
        when(goatRepository.countByStableId(1L)).thenReturn(8L);

        assertThatThrownBy(() -> goatService.save(goat)).isInstanceOf(RuntimeException.class);

        verify(goatRepository, never()).save(any(Goat.class));
    }

    @Test
    @DisplayName("Deletes the goat with the given id")
    void deleteDelegatesToRepository() {
        goatService.delete(5L);

        verify(goatRepository).deleteById(5L);
    }

    private Goat goat(String name, Long stableId) {
        Goat goat = new Goat();
        goat.setName(name);
        goat.setStableId(stableId);
        return goat;
    }
}
