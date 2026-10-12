package com.example.farm.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.Mockito.when;

import com.example.farm.model.Rabbit;
import com.example.farm.repository.RabbitRepository;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

@ExtendWith(MockitoExtension.class)
@DisplayName("RabbitService")
class RabbitServiceTest {

    @Mock
    private RabbitRepository rabbitRepository;

    @InjectMocks
    private RabbitService rabbitService;

    @Test
    @DisplayName("Returns all rabbits when at least one exists")
    void findAllReturnsRabbits() {
        when(rabbitRepository.findAll()).thenReturn(List.of(new Rabbit()));

        assertThat(rabbitService.findAll()).hasSize(1);
    }

    @Test
    @DisplayName("Returns null instead of an empty list when there are no rabbits (current behavior)")
    void findAllReturnsNullWhenEmpty() {
        when(rabbitRepository.findAll()).thenReturn(List.of());

        assertThat(rabbitService.findAll()).isNull();
    }

    @Test
    @DisplayName("Returns the rabbit with the given id")
    void findOneReturnsRabbit() {
        Rabbit rabbit = new Rabbit();
        when(rabbitRepository.findById(1L)).thenReturn(Optional.of(rabbit));

        assertThat(rabbitService.findOne(1L)).isSameAs(rabbit);
    }

    @Test
    @DisplayName("Returns null when the rabbit does not exist (current behavior)")
    void findOneReturnsNullWhenMissing() {
        when(rabbitRepository.findById(99L)).thenReturn(Optional.empty());

        assertThat(rabbitService.findOne(99L)).isNull();
    }

    @Test
    @DisplayName("Saves the rabbit and returns the stored instance")
    void saveReturnsStoredRabbit() {
        Rabbit rabbit = new Rabbit();
        when(rabbitRepository.save(rabbit)).thenReturn(rabbit);

        assertThat(rabbitService.save(rabbit)).isSameAs(rabbit);
    }

    @Test
    @DisplayName("Returns null when saving fails (current behavior)")
    void saveReturnsNullOnFailure() {
        Rabbit rabbit = new Rabbit();
        when(rabbitRepository.save(rabbit)).thenThrow(new IllegalStateException("database down"));

        assertThat(rabbitService.save(rabbit)).isNull();
    }
}
