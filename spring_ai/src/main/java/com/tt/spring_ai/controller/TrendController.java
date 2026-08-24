package com.tt.spring_ai.controller;

import com.tt.spring_ai.dto.TrendDto;
import com.tt.spring_ai.service.TrendService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/trends")
@CrossOrigin(origins = "*")
public class TrendController {

    private final TrendService trendService;

    public TrendController(TrendService trendService) {
        this.trendService = trendService;
    }

    @GetMapping("/recommend")
    public ResponseEntity<TrendDto> trendRecommend(@RequestParam String keyword) {
        TrendDto result = trendService.trendRecommend(keyword);
        return ResponseEntity.ok(result);
    }
}