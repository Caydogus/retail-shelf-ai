import os
from datetime import datetime
from typing import Dict, List
import json


class ReportGenerator:
    def __init__(self):
        self.upload_dir = os.getenv("UPLOAD_DIR", "./uploads")
    
    def generate_analysis_report(self, analysis_data: Dict):
        '''Generate detailed analysis report'''
        try:
            report = {
                'report_id': f"RPT_{analysis_data.get('id', 0)}_{int(datetime.now().timestamp())}",
                'generated_at': datetime.now().isoformat(),
                'analysis_summary': {
                    'total_products': analysis_data.get('total_products', 0),
                    'shelf_coverage': analysis_data.get('shelf_coverage', 0),
                    'visibility_score': analysis_data.get('visibility_score', 0),
                    'planogram_score': analysis_data.get('planogram_score', 0),
                    'total_score': analysis_data.get('total_score', 0)
                },
                'product_breakdown': analysis_data.get('product_counts', {}),
                'detections': analysis_data.get('detections', []),
                'color_analysis': analysis_data.get('color_analysis', {}),
                'recommendations': self._generate_recommendations(analysis_data)
            }
            
            return {'success': True, 'report': report}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _generate_recommendations(self, analysis_data: Dict) -> List[str]:
        '''Generate recommendations based on analysis'''
        recommendations = []
        
        coverage = analysis_data.get('shelf_coverage', 0)
        visibility = analysis_data.get('visibility_score', 0)
        planogram = analysis_data.get('planogram_score', 0)
        
        # Coverage recommendations
        if coverage < 50:
            recommendations.append("Raf doluluk oranı düşük. Daha fazla ürün yerleştirilmeli.")
        elif coverage > 90:
            recommendations.append("Raf çok dolu. Ürün görünürlüğü azalabilir.")
        
        # Visibility recommendations
        if visibility < 60:
            recommendations.append("Ürün görünürlüğü düşük. Ürünlerin konumu optimize edilmeli.")
        
        # Planogram recommendations
        if planogram < 70:
            recommendations.append("Planogram uyumu düşük. Ürün yerleşimi plana göre düzenlenmeli.")
        
        # Product distribution
        distribution = analysis_data.get('distribution', {})
        if distribution:
            left = distribution.get('left', 0)
            center = distribution.get('center', 0)
            right = distribution.get('right', 0)
            total = left + center + right
            
            if total > 0:
                center_ratio = center / total
                if center_ratio < 0.3:
                    recommendations.append("Merkez bölgede daha fazla ürün bulundurulmalı.")
        
        if not recommendations:
            recommendations.append("Raf düzeni optimum seviyede.")
        
        return recommendations
    
    def generate_training_report(self, model_data: Dict):
        '''Generate model training report'''
        try:
            report = {
                'report_id': f"TRN_{model_data.get('id', 0)}_{int(datetime.now().timestamp())}",
                'generated_at': datetime.now().isoformat(),
                'model_info': {
                    'model_name': model_data.get('name', ''),
                    'version': model_data.get('version', ''),
                    'status': model_data.get('status', '')
                },
                'training_config': model_data.get('training_config', {}),
                'metrics': {
                    'mAP50': model_data.get('mAP50', 0),
                    'mAP50_95': model_data.get('mAP50_95', 0),
                    'precision': model_data.get('precision', 0),
                    'recall': model_data.get('recall', 0)
                },
                'training_duration': self._calculate_duration(
                    model_data.get('training_started_at'),
                    model_data.get('training_completed_at')
                ),
                'performance_evaluation': self._evaluate_performance(model_data)
            }
            
            return {'success': True, 'report': report}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _calculate_duration(self, start_time, end_time):
        '''Calculate training duration'''
        if not start_time or not end_time:
            return "N/A"
        
        if isinstance(start_time, str):
            start_time = datetime.fromisoformat(start_time)
        if isinstance(end_time, str):
            end_time = datetime.fromisoformat(end_time)
        
        duration = end_time - start_time
        hours = duration.total_seconds() / 3600
        return f"{hours:.2f} hours"
    
    def _evaluate_performance(self, model_data: Dict) -> str:
        '''Evaluate model performance'''
        mAP50 = model_data.get('mAP50', 0)
        precision = model_data.get('precision', 0)
        recall = model_data.get('recall', 0)
        
        if mAP50 >= 0.9 and precision >= 0.85 and recall >= 0.85:
            return "Excellent - Model ready for production"
        elif mAP50 >= 0.75 and precision >= 0.70 and recall >= 0.70:
            return "Good - Model performs well"
        elif mAP50 >= 0.60:
            return "Fair - Model needs improvement"
        else:
            return "Poor - Consider retraining with more data"
    
    def generate_comparison_report(self, analyses: List[Dict]):
        '''Generate comparison report for multiple analyses'''
        try:
            if not analyses:
                return {'success': False, 'error': 'No analyses provided'}
            
            report = {
                'report_id': f"CMP_{int(datetime.now().timestamp())}",
                'generated_at': datetime.now().isoformat(),
                'total_analyses': len(analyses),
                'average_metrics': self._calculate_averages(analyses),
                'best_analysis': self._find_best(analyses),
                'worst_analysis': self._find_worst(analyses),
                'trend': self._analyze_trend(analyses)
            }
            
            return {'success': True, 'report': report}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _calculate_averages(self, analyses: List[Dict]) -> Dict:
        '''Calculate average metrics'''
        total = len(analyses)
        
        avg_coverage = sum(a.get('shelf_coverage', 0) for a in analyses) / total
        avg_visibility = sum(a.get('visibility_score', 0) for a in analyses) / total
        avg_total = sum(a.get('total_score', 0) for a in analyses) / total
        
        return {
            'shelf_coverage': round(avg_coverage, 2),
            'visibility_score': round(avg_visibility, 2),
            'total_score': round(avg_total, 2)
        }
    
    def _find_best(self, analyses: List[Dict]) -> Dict:
        '''Find best performing analysis'''
        best = max(analyses, key=lambda x: x.get('total_score', 0))
        return {
            'id': best.get('id'),
            'total_score': best.get('total_score'),
            'date': best.get('analysis_date')
        }
    
    def _find_worst(self, analyses: List[Dict]) -> Dict:
        '''Find worst performing analysis'''
        worst = min(analyses, key=lambda x: x.get('total_score', 0))
        return {
            'id': worst.get('id'),
            'total_score': worst.get('total_score'),
            'date': worst.get('analysis_date')
        }
    
    def _analyze_trend(self, analyses: List[Dict]) -> str:
        '''Analyze performance trend'''
        if len(analyses) < 2:
            return "Insufficient data for trend analysis"
        
        scores = [a.get('total_score', 0) for a in analyses]
        first_half_avg = sum(scores[:len(scores)//2]) / (len(scores)//2)
        second_half_avg = sum(scores[len(scores)//2:]) / (len(scores) - len(scores)//2)
        
        if second_half_avg > first_half_avg + 5:
            return "Improving"
        elif second_half_avg < first_half_avg - 5:
            return "Declining"
        else:
            return "Stable"
    
    def export_report_to_json(self, report: Dict, output_path: str):
        '''Export report to JSON file'''
        try:
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2)
            return {'success': True, 'output_path': output_path}
        except Exception as e:
            return {'success': False, 'error': str(e)}
