package com.example.farm.model;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.ForeignKey;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;

@Entity
@Table(name = "horses")
public class Horse extends Animal {

    @Column(name = "breed", nullable = false, length = 100)
    private String breed;

    @Column(name = "withers_height_cm", nullable = false)
    private Integer withersHeightCm;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "stable_id", foreignKey = @ForeignKey(name = "fk_horses_stable_id"))
    private Stable stable;

    public String getBreed() {
        return breed;
    }

    public void setBreed(String breed) {
        this.breed = breed;
    }

    public Integer getWithersHeightCm() {
        return withersHeightCm;
    }

    public void setWithersHeightCm(Integer withersHeightCm) {
        this.withersHeightCm = withersHeightCm;
    }

    public Stable getStable() {
        return stable;
    }

    public void setStable(Stable stable) {
        this.stable = stable;
    }
}
