package com.example.farm.model;

import jakarta.persistence.*;

@Entity
public class Goat {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String name;

    private double weight;

    private boolean hornFlag;

    @Column(name = "DailyMilkLiters")
    private double dailyMilkLiters;

    private Long stableId;

    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public double getWeight() {
        return weight;
    }

    public void setWeight(double weight) {
        this.weight = weight;
    }

    public boolean isHornFlag() {
        return hornFlag;
    }

    public void setHornFlag(boolean hornFlag) {
        this.hornFlag = hornFlag;
    }

    public double getDailyMilkLiters() {
        return dailyMilkLiters;
    }

    public void setDailyMilkLiters(double dailyMilkLiters) {
        this.dailyMilkLiters = dailyMilkLiters;
    }

    public Long getStableId() {
        return stableId;
    }

    public void setStableId(Long stableId) {
        this.stableId = stableId;
    }
}
