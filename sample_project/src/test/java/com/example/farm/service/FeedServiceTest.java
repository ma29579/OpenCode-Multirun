package com.example.farm.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.within;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.example.farm.model.Feed;
import com.example.farm.repository.FeedRepository;
import java.time.LocalDate;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

/**
 * The service keeps a static cache, so every test uses its own feed id to stay independent.
 */
@ExtendWith(MockitoExtension.class)
@DisplayName("FeedService")
class FeedServiceTest {

    @Mock
    private FeedRepository feedRepository;

    @InjectMocks
    private FeedService feedService;

    @Test
    @DisplayName("Returns all feed from the repository")
    void findAllReturnsAllFeed() {
        when(feedRepository.findAll()).thenReturn(List.of(feed(1000L, 50.0, "2030-01-01")));

        assertThat(feedService.findAll()).hasSize(1);
    }

    @Test
    @DisplayName("Loads a feed from the repository only once and serves it from the cache afterwards")
    void findOneUsesCache() {
        Feed feed = feed(101L, 50.0, "2030-01-01");
        when(feedRepository.findById(101L)).thenReturn(Optional.of(feed));

        assertThat(feedService.findOne(101L)).isSameAs(feed);
        assertThat(feedService.findOne(101L)).isSameAs(feed);

        verify(feedRepository, times(1)).findById(101L);
    }

    @Test
    @DisplayName("Returns null when the feed does not exist")
    void findOneReturnsNullWhenMissing() {
        when(feedRepository.findById(102L)).thenReturn(Optional.empty());

        assertThat(feedService.findOne(102L)).isNull();
    }

    @Test
    @DisplayName("Saves the feed through the repository")
    void saveDelegatesToRepository() {
        Feed feed = feed(null, 10.0, "2030-01-01");
        when(feedRepository.save(feed)).thenReturn(feed);

        assertThat(feedService.save(feed)).isSameAs(feed);
    }

    @Test
    @DisplayName("Reduces the stock by the consumed amount and saves the feed")
    void consumeReducesQuantity() {
        Feed feed = feed(103L, 100.0, "2030-01-01");
        when(feedRepository.findById(103L)).thenReturn(Optional.of(feed));
        when(feedRepository.save(feed)).thenReturn(feed);

        Feed result = feedService.consume(103L, 12.5);

        assertThat(result.getQuantityKg()).isEqualTo(87.5);
        verify(feedRepository).save(feed);
    }

    @Test
    @DisplayName("Returns null when consuming a feed that does not exist")
    void consumeReturnsNullWhenMissing() {
        when(feedRepository.findById(104L)).thenReturn(Optional.empty());

        assertThat(feedService.consume(104L, 5.0)).isNull();
    }

    @Test
    @DisplayName("Reports a feed with a past expiration date as expired")
    void isExpiredForPastDate() {
        Feed feed = feed(null, 1.0, LocalDate.now().minusDays(1).toString());

        assertThat(feedService.isExpired(feed)).isTrue();
    }

    @Test
    @DisplayName("Reports a feed with a future expiration date as not expired")
    void isExpiredForFutureDate() {
        Feed feed = feed(null, 1.0, LocalDate.now().plusDays(30).toString());

        assertThat(feedService.isExpired(feed)).isFalse();
    }

    @Test
    @DisplayName("Treats a feed with an unreadable expiration date as not expired")
    void isExpiredForInvalidDate() {
        assertThat(feedService.isExpired(feed(null, 1.0, "next year"))).isFalse();
        assertThat(feedService.isExpired(feed(null, 1.0, null))).isFalse();
    }

    @Test
    @DisplayName("Calculates zero monthly cost when there are no animals")
    void monthlyCostIsZeroWithoutAnimals() {
        assertThat(feedService.calculateMonthlyCost(0, 0, 0, 0, 0, 0, 0)).isZero();
    }

    @Test
    @DisplayName("Calculates the monthly cost of a single horse")
    void monthlyCostForOneHorse() {
        assertThat(feedService.calculateMonthlyCost(1, 0, 0, 0, 0, 0, 0)).isCloseTo(105.0, within(0.001));
    }

    @Test
    @DisplayName("Applies a 5 percent discount for more than five horses")
    void monthlyCostAppliesHorseDiscount() {
        assertThat(feedService.calculateMonthlyCost(6, 0, 0, 0, 0, 0, 0)).isCloseTo(598.5, within(0.001));
    }

    @Test
    @DisplayName("Calculates the monthly cost of cows and rabbits")
    void monthlyCostForCowsAndRabbits() {
        double cost = feedService.calculateMonthlyCost(0, 2, 0, 0, 0, 10, 0);

        assertThat(cost).isCloseTo(285.0 + 18.0, within(0.001));
    }

    private Feed feed(Long id, double quantityKg, String expirationDate) {
        Feed feed = new Feed();
        feed.setId(id);
        feed.setName("Hay");
        feed.setQuantityKg(quantityKg);
        feed.setExpirationDate(expirationDate);
        return feed;
    }
}
