package com.example.farm.model;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

@Entity
@Table(name = "Sheep")
public class Sheep {

    @Id
    @GeneratedValue
    private Long id;

    @Column(name = "SheepName")
    private String name;

    private String birthDate;

    private double woolYieldKg;

    private String stableName;

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

    public String getBirthDate() {
        return birthDate;
    }

    public void setBirthDate(String birthDate) {
        this.birthDate = birthDate;
    }

    public double getWoolYieldKg() {
        return woolYieldKg;
    }

    public void setWoolYieldKg(double woolYieldKg) {
        this.woolYieldKg = woolYieldKg;
    }

    public String getStableName() {
        return stableName;
    }

    public void setStableName(String stableName) {
        this.stableName = stableName;
    }
}
