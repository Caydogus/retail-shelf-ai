import numpy as np


class ScoringEngine:
    def __init__(self, scoring_rules: list = None):
        self.scoring_rules = scoring_rules or []
        self.default_weights = {
            'shelf_coverage': 0.25,
            'product_visibility': 0.30,
            'planogram_compliance': 0.25,
            'color_match': 0.20
        }
    
    def calculate_shelf_coverage_score(self, coverage_percent: float):
        """Score based on shelf coverage percentage"""
        # Ideal coverage is 70-85%
        if 70 <= coverage_percent <= 85:
            score = 100
        elif coverage_percent < 70:
            score = (coverage_percent / 70) * 100
        else:
            score = 100 - ((coverage_percent - 85) * 2)
        
        return max(0, min(100, score))
    
    def calculate_visibility_score(self, visibility_score: float):
        """Score based on product visibility"""
        return min(100, visibility_score)
    
    def calculate_planogram_score(self, expected_distribution: dict, actual_distribution: dict):
        """Score based on planogram compliance"""
        if not expected_distribution or not actual_distribution:
            return 50.0
        
        total_diff = 0
        for position in ['left', 'center', 'right']:
            expected = expected_distribution.get(position, 0)
            actual = actual_distribution.get(position, 0)
            diff = abs(expected - actual)
            total_diff += diff
        
        # Convert difference to score (lower diff = higher score)
        max_diff = sum(expected_distribution.values()) if expected_distribution else 100
        score = (1 - (total_diff / max_diff)) * 100 if max_diff > 0 else 50
        
        return max(0, min(100, score))
    
    def calculate_color_match_score(self, color_matches: dict):
        """Score based on color matching"""
        if not color_matches:
            return 50.0
        
        avg_score = np.mean(list(color_matches.values()))
        return round(avg_score, 2)
    
    def calculate_total_score(self, metrics: dict, weights: dict = None):
        """Calculate weighted total score"""
        weights = weights or self.default_weights
        
        scores = {
            'shelf_coverage': self.calculate_shelf_coverage_score(
                metrics.get('shelf_coverage', 0)
            ),
            'product_visibility': self.calculate_visibility_score(
                metrics.get('visibility_score', 0)
            ),
            'planogram_compliance': self.calculate_planogram_score(
                metrics.get('expected_distribution', {}),
                metrics.get('actual_distribution', {})
            ),
            'color_match': self.calculate_color_match_score(
                metrics.get('color_matches', {})
            )
        }
        
        # Calculate weighted total
        total_score = sum(
            scores[key] * weights.get(key, 0.25)
            for key in scores.keys()
        )
        
        return {
            'total_score': round(total_score, 2),
            'component_scores': scores,
            'weights_used': weights
        }
