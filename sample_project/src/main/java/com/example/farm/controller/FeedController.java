package com.example.farm.controller;

import com.example.farm.model.Feed;
import com.example.farm.service.FeedService;
import java.util.List;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/feeds")
public class FeedController {

    @Autowired
    private FeedService feedService;

    @GetMapping
    public List<Feed> all() {
        return feedService.findAll();
    }

    @PostMapping
    public Feed create(@RequestBody Feed feed) {
        return feedService.save(feed);
    }

    @GetMapping("/consume")
    public Feed consume(@RequestParam Long id, @RequestParam double amount) {
        return feedService.consume(id, amount);
    }

    @GetMapping("/cost")
    public double cost(@RequestParam int h, @RequestParam int c, @RequestParam int p, @RequestParam int g,
            @RequestParam int s, @RequestParam int r, @RequestParam int d) {
        return feedService.calculateMonthlyCost(h, c, p, g, s, r, d);
    }
}
