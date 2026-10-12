package com.example.farm.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.example.farm.model.Sheep;
import com.example.farm.repository.SheepRepository;
import java.util.List;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

@ExtendWith(MockitoExtension.class)
@DisplayName("SheepService")
class SheepServiceTest {

    @Mock
    private SheepRepository sheepRepository;

    private SheepService sheepService;

    @BeforeEach
    void setUp() {
        sheepService = new SheepService(sheepRepository);
    }

    @Test
    @DisplayName("Returns all sheep from the repository")
    void findAllReturnsAllSheep() {
        when(sheepRepository.findAll()).thenReturn(List.of(sheep("Shaun", "Meadow")));

        assertThat(sheepService.findAll()).hasSize(1);
    }

    @Test
    @DisplayName("Rejects a new sheep without a name with status 400")
    void addRejectsMissingName() {
        ResponseEntity<?> response = sheepService.add(sheep(null, "Meadow"));

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.BAD_REQUEST);
        verify(sheepRepository, never()).save(any(Sheep.class));
    }

    @Test
    @DisplayName("Rejects a new sheep with an empty name with status 400")
    void addRejectsEmptyName() {
        ResponseEntity<?> response = sheepService.add(sheep("", "Meadow"));

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.BAD_REQUEST);
    }

    @Test
    @DisplayName("Rejects a new sheep with status 409 when its stable holds twelve sheep")
    void addRejectsSheepWhenStableIsFull() {
        when(sheepRepository.countByStableName("Meadow")).thenReturn(12L);

        ResponseEntity<?> response = sheepService.add(sheep("Shaun", "Meadow"));

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.CONFLICT);
        verify(sheepRepository, never()).save(any(Sheep.class));
    }

    @Test
    @DisplayName("Saves a new sheep and returns it with status 200")
    void addSavesSheep() {
        Sheep sheep = sheep("Shaun", "Meadow");
        when(sheepRepository.countByStableName("Meadow")).thenReturn(3L);
        when(sheepRepository.save(sheep)).thenReturn(sheep);

        ResponseEntity<?> response = sheepService.add(sheep);

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(response.getBody()).isSameAs(sheep);
    }

    @Test
    @DisplayName("Saves a new sheep that has no stable without checking any capacity")
    void addSavesSheepWithoutStable() {
        Sheep sheep = sheep("Shaun", null);
        when(sheepRepository.save(sheep)).thenReturn(sheep);

        ResponseEntity<?> response = sheepService.add(sheep);

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
        verify(sheepRepository, never()).countByStableName(any());
    }

    @Test
    @DisplayName("Returns status 404 when updating a sheep that does not exist")
    void updateReturnsNotFound() {
        when(sheepRepository.existsById(99L)).thenReturn(false);

        ResponseEntity<?> response = sheepService.update(99L, sheep("Shaun", "Meadow"));

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.NOT_FOUND);
    }

    @Test
    @DisplayName("Rejects an update without a name with status 400")
    void updateRejectsMissingName() {
        when(sheepRepository.existsById(1L)).thenReturn(true);

        ResponseEntity<?> response = sheepService.update(1L, sheep(null, "Meadow"));

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.BAD_REQUEST);
    }

    @Test
    @DisplayName("Rejects an update with status 409 when the target stable is full")
    void updateRejectsFullStable() {
        when(sheepRepository.existsById(1L)).thenReturn(true);
        when(sheepRepository.countByStableName("Meadow")).thenReturn(12L);

        ResponseEntity<?> response = sheepService.update(1L, sheep("Shaun", "Meadow"));

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.CONFLICT);
    }

    @Test
    @DisplayName("Saves the update using the id from the path")
    void updateSavesSheepWithPathId() {
        Sheep sheep = sheep("Shaun", "Meadow");
        when(sheepRepository.existsById(1L)).thenReturn(true);
        when(sheepRepository.countByStableName("Meadow")).thenReturn(1L);
        when(sheepRepository.save(sheep)).thenReturn(sheep);

        ResponseEntity<?> response = sheepService.update(1L, sheep);

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(sheep.getId()).isEqualTo(1L);
    }

    @Test
    @DisplayName("Removes the sheep and confirms with status 200")
    void removeDeletesSheep() {
        ResponseEntity<?> response = sheepService.remove(4L);

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
        verify(sheepRepository).deleteById(4L);
    }

    private Sheep sheep(String name, String stableName) {
        Sheep sheep = new Sheep();
        sheep.setName(name);
        sheep.setStableName(stableName);
        return sheep;
    }
}
