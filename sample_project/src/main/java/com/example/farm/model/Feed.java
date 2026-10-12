package com.example.farm.model;

import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

@Entity
@Table(name = "Feed")
public class Feed {

    @Id
    @GeneratedValue
    private Long id;

    private String name;

    private FeedType type;

    private double quantityKg;

    private double pricePerKg;

    // comma separated, e.g. "HORSE,COW,DONKEY"
    private String allowedAnimals;

    // format yyyy-MM-dd
    private String expirationDate;

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

    public FeedType getType() {
        return type;
    }

    public void setType(FeedType type) {
        this.type = type;
    }

    public double getQuantityKg() {
        return quantityKg;
    }

    public void setQuantityKg(double quantityKg) {
        this.quantityKg = quantityKg;
    }

    public double getPricePerKg() {
        return pricePerKg;
    }

    public void setPricePerKg(double pricePerKg) {
        this.pricePerKg = pricePerKg;
    }

    public String getAllowedAnimals() {
        return allowedAnimals;
    }

    public void setAllowedAnimals(String allowedAnimals) {
        this.allowedAnimals = allowedAnimals;
    }

    public String getExpirationDate() {
        return expirationDate;
    }

    public void setExpirationDate(String expirationDate) {
        this.expirationDate = expirationDate;
    }
}
