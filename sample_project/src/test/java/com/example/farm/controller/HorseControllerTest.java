package com.example.farm.controller;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.jayway.jsonpath.JsonPath;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

@SpringBootTest
@AutoConfigureMockMvc
@DisplayName("Horse API")
class HorseControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @Test
    @DisplayName("Creates a horse in a stable and answers 409 when the stable is full")
    void createsHorseInStableAndRejectsHorseWhenStableIsFull() throws Exception {
        String stableJson = mockMvc.perform(post("/api/v1/stables")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"name\":\"Main barn\",\"capacity\":1,\"type\":\"HORSE_STABLE\"}"))
                .andExpect(status().isCreated())
                .andReturn().getResponse().getContentAsString();
        int stableId = JsonPath.read(stableJson, "$.id");

        String horseJson = "{\"name\":\"Blitz\",\"birthDate\":\"2018-04-12\",\"weightKg\":520.5,"
                + "\"breed\":\"Haflinger\",\"withersHeightCm\":148,\"stableId\":" + stableId + "}";

        mockMvc.perform(post("/api/v1/horses").contentType(MediaType.APPLICATION_JSON).content(horseJson))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.name").value("Blitz"));

        mockMvc.perform(post("/api/v1/horses").contentType(MediaType.APPLICATION_JSON).content(horseJson))
                .andExpect(status().isConflict());

        mockMvc.perform(get("/api/v1/horses"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.content.length()").value(1));
    }

    @Test
    @DisplayName("Answers 400 when the horse data is invalid")
    void rejectsInvalidHorse() throws Exception {
        mockMvc.perform(post("/api/v1/horses").contentType(MediaType.APPLICATION_JSON).content("{}"))
                .andExpect(status().isBadRequest());
    }
}
