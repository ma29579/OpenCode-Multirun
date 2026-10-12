package com.example.farm.exception;

/** Thrown when a request violates a rule of the domain. */
public class ConflictException extends RuntimeException {

    public ConflictException(String message) {
        super(message);
    }
}
