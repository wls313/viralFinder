package com.tt.spring_ai.controller;

import com.tt.spring_ai.dto.TrendAnalysisResult;
import com.tt.spring_ai.service.TrendAnalysisService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/trends")
@CrossOrigin(origins = "*")
public class TrendController {

    private final TrendAnalysisService trendAnalysisService;

    public TrendController(TrendAnalysisService trendAnalysisService) {
        this.trendAnalysisService = trendAnalysisService;
    }

    @GetMapping("/recommend")
    public ResponseEntity<TrendAnalysisResult> trendRecommend(
            @RequestParam String keyword,
            @RequestParam(defaultValue = "1w") String period) {
        TrendAnalysisResult result = trendAnalysisService.analyze(keyword, period);
        return ResponseEntity.ok(result);
    }
}
