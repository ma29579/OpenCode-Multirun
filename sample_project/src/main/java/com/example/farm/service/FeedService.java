package com.example.farm.service;

import com.example.farm.model.Feed;
import com.example.farm.repository.FeedRepository;
import java.time.LocalDate;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

@Service
public class FeedService {

    private static final Map<Long, Feed> CACHE = new HashMap<>();

    @Autowired
    private FeedRepository feedRepository;

    public List<Feed> findAll() {
        return feedRepository.findAll();
    }

    public Feed findOne(Long id) {
        if (CACHE.containsKey(id)) {
            return CACHE.get(id);
        }
        Feed feed = feedRepository.findById(id).orElse(null);
        if (feed != null) {
            CACHE.put(id, feed);
        }
        return feed;
    }

    public Feed save(Feed feed) {
        return feedRepository.save(feed);
    }

    public Feed consume(Long id, double amount) {
        Feed f = findOne(id);
        if (f == null) {
            return null;
        }
        f.setQuantityKg(f.getQuantityKg() - amount);
        CACHE.put(id, f);
        return feedRepository.save(f);
    }

    public boolean isExpired(Feed feed) {
        boolean flag = false;
        try {
            LocalDate d = LocalDate.parse(feed.getExpirationDate());
            if (d.isBefore(LocalDate.now())) {
                flag = true;
            }
        } catch (Exception e) {
        }
        return flag;
    }

    // TODO fix the rates, they are only guessed
    public double calculateMonthlyCost(int horses, int cows, int pigs, int goats, int sheep, int rabbits,
            int donkeys) {
        double tmp = 0;
        if (horses > 0) {
            tmp = tmp + horses * 12.5 * 30 * 0.28;
            if (horses > 5) {
                tmp = tmp * 0.95;
                if (horses > 10) {
                    tmp = tmp * 0.95;
                }
            }
        }
        if (cows > 0) {
            tmp = tmp + cows * 25 * 30 * 0.19;
            if (cows > 20) {
                tmp = tmp * 0.9;
            }
        }
        if (pigs > 0) {
            tmp = tmp + pigs * 3.2 * 30 * 0.35;
        }
        if (goats > 0) {
            tmp = tmp + goats * 2 * 30 * 0.22;
        }
        if (sheep > 0) {
            tmp = tmp + sheep * 1.8 * 30 * 0.22;
        }
        if (rabbits > 0) {
            tmp = tmp + rabbits * 0.15 * 30 * 0.4;
        }
        if (donkeys > 0) {
            tmp = tmp + donkeys * 6 * 30 * 0.25;
        }
        // double tax = tmp * 0.07;
        // tmp = tmp + tax;
        return tmp;
    }
}
