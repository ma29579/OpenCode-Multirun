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
@Table(name = "donkeys")
public class Donkey extends Animal {

    @Column(name = "breed", nullable = false, length = 100)
    private String breed;

    @Column(name = "max_load_kg", nullable = false, precision = 6, scale = 2)
    private BigDecimal maxLoadKg;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "stable_id", foreignKey = @ForeignKey(name = "fk_donkeys_stable_id"))
    private Stable stable;

    public String getBreed() {
        return breed;
    }

    public void setBreed(String breed) {
        this.breed = breed;
    }

    public BigDecimal getMaxLoadKg() {
        return maxLoadKg;
    }

    public void setMaxLoadKg(BigDecimal maxLoadKg) {
        this.maxLoadKg = maxLoadKg;
    }

    public Stable getStable() {
        return stable;
    }

    public void setStable(Stable stable) {
        this.stable = stable;
    }
}
