package com.example.farm.model;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.Table;
import jakarta.persistence.UniqueConstraint;

@Entity
@Table(name = "stables",
        uniqueConstraints = @UniqueConstraint(name = "uq_stables_name", columnNames = "name"))
public class Stable extends AuditedEntity {

    @Column(name = "name", nullable = false, length = 100)
    private String name;

    @Column(name = "capacity", nullable = false)
    private int capacity;

    @Enumerated(EnumType.STRING)
    @Column(name = "type", nullable = false, length = 30)
    private StableType type;

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public int getCapacity() {
        return capacity;
    }

    public void setCapacity(int capacity) {
        this.capacity = capacity;
    }

    public StableType getType() {
        return type;
    }

    public void setType(StableType type) {
        this.type = type;
    }
}
