package com.example.farm.model;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.ForeignKey;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;
import java.math.BigDecimal;

@Entity
@Table(name = "cows")
public class Cow extends Animal {

    @Column(name = "breed", nullable = false, length = 100)
    private String breed;

    @Column(name = "daily_milk_liters", nullable = false, precision = 6, scale = 2)
    private BigDecimal dailyMilkLiters;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "stable_id", foreignKey = @ForeignKey(name = "fk_cows_stable_id"))
    private Stable stable;

    public String getBreed() {
        return breed;
    }

    public void setBreed(String breed) {
        this.breed = breed;
    }

    public BigDecimal getDailyMilkLiters() {
        return dailyMilkLiters;
    }

    public void setDailyMilkLiters(BigDecimal dailyMilkLiters) {
        this.dailyMilkLiters = dailyMilkLiters;
    }

    public Stable getStable() {
        return stable;
    }

    public void setStable(Stable stable) {
        this.stable = stable;
    }
}
