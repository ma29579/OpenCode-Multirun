package com.example.farm.model;

import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;

@Entity
@Table(name = "tbl_pig")
public class Pig {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Integer pigId;

    private String name;

    private String breed;

    private int ageInMonths;

    private double targetWeightKg;

    @ManyToOne
    private Stable stable;

    public Integer getPigId() {
        return pigId;
    }

    public void setPigId(Integer pigId) {
        this.pigId = pigId;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getBreed() {
        return breed;
    }

    public void setBreed(String breed) {
        this.breed = breed;
    }

    public int getAgeInMonths() {
        return ageInMonths;
    }

    public void setAgeInMonths(int ageInMonths) {
        this.ageInMonths = ageInMonths;
    }

    public double getTargetWeightKg() {
        return targetWeightKg;
    }

    public void setTargetWeightKg(double targetWeightKg) {
        this.targetWeightKg = targetWeightKg;
    }

    public Stable getStable() {
        return stable;
    }

    public void setStable(Stable stable) {
        this.stable = stable;
    }
}
