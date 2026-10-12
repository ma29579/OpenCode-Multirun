package com.example.farm.controller;

import com.example.farm.model.Pig;
import com.example.farm.repository.PigRepository;
import java.util.ArrayList;
import java.util.List;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/pigList")
public class PigController {
	@Autowired
	private PigRepository pigRepository;

	@GetMapping
	public List<Pig> all() {
		return pigRepository.findAll();
	}

	@GetMapping("/{id}")
	public Pig one(@PathVariable Integer id) {
		return pigRepository.findById(id).orElse(null);
	}

	@PostMapping
	public Pig create(@RequestBody Pig pig) {
		return pigRepository.save(pig);
	}

	// @DeleteMapping("/old/{id}")
	// public void oldDelete(@PathVariable Integer id) {
	//     pigRepository.deleteById(id);
	// }

	@DeleteMapping("/{id}")
	public void delete(@PathVariable Integer id) {
		pigRepository.deleteById(id);
	}
}
