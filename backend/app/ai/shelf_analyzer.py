import numpy as np
import cv2
from collections import Counter
from typing import List, Dict, Tuple


class ShelfAnalyzer:
    """
    Gelişmiş Raf Analiz Sistemi
    - ROI (Raf Gözü) bazlı analiz
    - Klasik görüntü işleme metrikleri
    - YOLO ile entegre çalışır
    """
    
    def __init__(self, image_shape: tuple, eye_count: int = 3):
        """
        Args:
            image_shape: (height, width, channels)
            eye_count: Raf kaç göze bölünecek (default: 3)
        """
        self.image_height = image_shape[0]
        self.image_width = image_shape[1]
        self.eye_count = eye_count
        self.eyes = self._create_roi_regions()
    
    def _create_roi_regions(self) -> List[Dict]:
        """Rafı dikey olarak eye_count kadar göze böl"""
        eyes = []
        eye_height = self.image_height // self.eye_count
        
        for i in range(self.eye_count):
            y1 = i * eye_height
            y2 = (i + 1) * eye_height if i < self.eye_count - 1 else self.image_height
            
            eyes.append({
                'id': i + 1,
                'name': f'Göz {i + 1}',
                'region': {
                    'y1': y1,
                    'y2': y2,
                    'x1': 0,
                    'x2': self.image_width
                },
                'height': y2 - y1,
                'width': self.image_width
            })
        
        return eyes
    
    # ========================================================================
    # KLASİK GÖRÜNTÜ İŞLEME METRİKLERİ (AI'sız Analiz)
    # ========================================================================
    
    def calculate_edge_density(self, roi_image: np.ndarray) -> float:
        """Kenar yoğunluğu hesapla (raf doluluğu için)"""
        if roi_image is None or roi_image.size == 0:
            return 0.0
        
        gray = cv2.cvtColor(roi_image, cv2.COLOR_BGR2GRAY) if len(roi_image.shape) == 3 else roi_image
        edges = cv2.Canny(gray, 50, 150)
        edge_pixels = np.sum(edges > 0)
        total_pixels = edges.shape[0] * edges.shape[1]
        
        density = (edge_pixels / total_pixels) * 100
        return round(density, 2)
    
    def calculate_texture_variance(self, roi_image: np.ndarray) -> float:
        """Doku varyansı hesapla (karmaşıklık için)"""
        if roi_image is None or roi_image.size == 0:
            return 0.0
        
        gray = cv2.cvtColor(roi_image, cv2.COLOR_BGR2GRAY) if len(roi_image.shape) == 3 else roi_image
        variance = np.var(gray)
        
        return round(variance, 2)
    
    def calculate_luminance(self, roi_image: np.ndarray) -> float:
        """Parlaklık seviyesi hesapla"""
        if roi_image is None or roi_image.size == 0:
            return 0.0
        
        gray = cv2.cvtColor(roi_image, cv2.COLOR_BGR2GRAY) if len(roi_image.shape) == 3 else roi_image
        mean_luminance = np.mean(gray)
        
        return round(mean_luminance, 2)
    
    def calculate_color_variance(self, roi_image: np.ndarray) -> float:
        """Renk çeşitliliği hesapla"""
        if roi_image is None or roi_image.size == 0:
            return 0.0
        
        if len(roi_image.shape) == 3:
            hsv = cv2.cvtColor(roi_image, cv2.COLOR_BGR2HSV)
            h_variance = np.var(hsv[:, :, 0])
            return round(h_variance, 2)
        
        return 0.0
    
    def analyze_roi_classic(self, roi_image: np.ndarray) -> Dict:
        """Bir ROI için klasik görüntü işleme analizi (AI'sız)"""
        return {
            'edge_density': self.calculate_edge_density(roi_image),
            'texture_variance': self.calculate_texture_variance(roi_image),
            'luminance': self.calculate_luminance(roi_image),
            'color_variance': self.calculate_color_variance(roi_image),
            'estimated_fullness': self._estimate_fullness_classic(roi_image)
        }
    
    def _estimate_fullness_classic(self, roi_image: np.ndarray) -> float:
        """AI'sız doluluk tahmini (edge + texture kombinasyonu)"""
        if roi_image is None or roi_image.size == 0:
            return 0.0
        
        edge_density = self.calculate_edge_density(roi_image)
        texture_var = self.calculate_texture_variance(roi_image)
        
        # Normalizasyon ve ağırlıklandırma
        edge_score = min(edge_density / 10, 10) * 5  # 0-50 arası
        texture_score = min(texture_var / 100, 10) * 5  # 0-50 arası
        
        fullness = edge_score + texture_score
        return round(min(fullness, 100), 2)
    
    # ========================================================================
    # YOLO TABANLI METRİKLER
    # ========================================================================
    
    def calculate_shelf_coverage(self, detections: list) -> float:
        """Raf doluluk oranı (YOLO bazlı)"""
        if not detections:
            return 0.0
        
        total_area = self.image_height * self.image_width
        product_area = 0
        
        for det in detections:
            bbox = det.get('bbox', {})
            if not bbox:
                continue
            
            width = bbox.get('x2', 0) - bbox.get('x1', 0)
            height = bbox.get('y2', 0) - bbox.get('y1', 0)
            product_area += width * height
        
        coverage = (product_area / total_area) * 100
        return round(coverage, 2)
    
    def count_products(self, detections: list) -> Dict:
        """Ürün sayımı (sınıf bazında)"""
        if not detections:
            return {}
        
        class_names = [det.get('class', 'unknown') for det in detections]
        counts = Counter(class_names)
        return dict(counts)
    
    def analyze_product_distribution(self, detections: list) -> Dict:
        """Yatay dağılım analizi"""
        if not detections:
            return {'left': 0, 'center': 0, 'right': 0}
        
        distribution = {'left': 0, 'center': 0, 'right': 0}
        
        for det in detections:
            x_center = det.get('x', 0)
            x_normalized = x_center / self.image_width
            
            if x_normalized < 0.33:
                distribution['left'] += 1
            elif x_normalized < 0.66:
                distribution['center'] += 1
            else:
                distribution['right'] += 1
        
        return distribution
    
    def calculate_visibility_score(self, detections: list) -> float:
        """Görünürlük skoru hesapla"""
        if not detections:
            return 0.0
        
        scores = []
        for det in detections:
            bbox = det.get('bbox', {})
            if not bbox:
                continue
            
            width = bbox.get('x2', 0) - bbox.get('x1', 0)
            height = bbox.get('y2', 0) - bbox.get('y1', 0)
            area = width * height
            
            # Normalize area
            normalized_area = area / (self.image_height * self.image_width)
            
            # Confidence factor
            confidence = det.get('confidence', 0)
            
            # Position factor
            x_center = det.get('x', 0)
            x_normalized = x_center / self.image_width
            center_factor = 1 - abs(0.5 - x_normalized)
            
            score = (normalized_area * 0.4 + confidence * 0.4 + center_factor * 0.2) * 100
            scores.append(score)
        
        avg_score = np.mean(scores) if scores else 0
        return round(avg_score, 2)
    
    # ========================================================================
    # ROI (RAF GÖZÜ) BAZLI ANALİZ
    # ========================================================================
    
    def assign_detections_to_eyes(self, detections: list) -> Dict[int, List]:
        """Tespit edilen ürünleri raf gözlerine ata"""
        eye_detections = {eye['id']: [] for eye in self.eyes}
        
        for det in detections:
            y_center = det.get('y', 0)
            
            # Hangi göze ait?
            for eye in self.eyes:
                if eye['region']['y1'] <= y_center < eye['region']['y2']:
                    eye_detections[eye['id']].append(det)
                    break
        
        return eye_detections
    
    def analyze_eye(self, eye_id: int, eye_detections: List, roi_image: np.ndarray = None) -> Dict:
        """Tek bir raf gözü için tam analiz"""
        eye_info = self.eyes[eye_id - 1]
        
        analysis = {
            'eye_id': eye_id,
            'eye_name': eye_info['name'],
            'region': eye_info['region'],
            'total_products': len(eye_detections),
            'product_counts': self.count_products(eye_detections)
        }
        
        # YOLO bazlı metrikler
        if eye_detections:
            eye_area = eye_info['height'] * eye_info['width']
            product_area = sum(
                (det['bbox']['x2'] - det['bbox']['x1']) * (det['bbox']['y2'] - det['bbox']['y1'])
                for det in eye_detections if 'bbox' in det
            )
            analysis['coverage'] = round((product_area / eye_area) * 100, 2)
            analysis['avg_confidence'] = round(
                np.mean([det.get('confidence', 0) for det in eye_detections]) * 100, 1
            )
        else:
            analysis['coverage'] = 0.0
            analysis['avg_confidence'] = 0.0
        
        # Klasik CV metrikleri (eğer görüntü verildiyse)
        if roi_image is not None:
            classic_metrics = self.analyze_roi_classic(roi_image)
            analysis['classic_metrics'] = classic_metrics
            
            # Hibrit skor: YOLO + Klasik
            yolo_score = analysis['coverage']
            classic_score = classic_metrics['estimated_fullness']
            analysis['hybrid_score'] = round((yolo_score * 0.6 + classic_score * 0.4), 2)
        else:
            analysis['hybrid_score'] = analysis['coverage']
        
        return analysis
    
    def extract_roi_image(self, full_image: np.ndarray, eye_id: int) -> np.ndarray:
        """Tam görüntüden bir raf gözünü çıkar"""
        eye = self.eyes[eye_id - 1]
        roi = full_image[
            eye['region']['y1']:eye['region']['y2'],
            eye['region']['x1']:eye['region']['x2']
        ]
        return roi
    
    # ========================================================================
    # ANA ANALİZ FONKSİYONU
    # ========================================================================
    
    def analyze_shelf(self, detections: list, full_image: np.ndarray = None) -> Dict:
        """
        Komple raf analizi
        
        Args:
            detections: YOLO tespit listesi
            full_image: Tam raf görüntüsü (opsiyonel, klasik metrikler için)
        
        Returns:
            Yapılandırılmış analiz sonucu
        """
        # Ürünleri gözlere ata
        eye_detections = self.assign_detections_to_eyes(detections)
        
        # Her göz için analiz
        eye_analyses = []
        for eye_id in range(1, self.eye_count + 1):
            roi_image = None
            if full_image is not None:
                roi_image = self.extract_roi_image(full_image, eye_id)
            
            eye_analysis = self.analyze_eye(eye_id, eye_detections[eye_id], roi_image)
            eye_analyses.append(eye_analysis)
        
        # Genel raf metrikleri
        analysis = {
            'version': '2.0',
            'analysis_mode': 'hybrid',  # YOLO + Classic CV
            'eye_count': self.eye_count,
            'eyes': eye_analyses,
            'summary': {
                'total_products': len(detections),
                'product_counts': self.count_products(detections),
                'shelf_coverage': self.calculate_shelf_coverage(detections),
                'distribution': self.analyze_product_distribution(detections),
                'visibility_score': self.calculate_visibility_score(detections)
            }
        }
        
        # Ağırlıklı genel skor
        if eye_analyses:
            weighted_scores = [eye['hybrid_score'] for eye in eye_analyses]
            analysis['summary']['total_score'] = round(np.mean(weighted_scores), 2)
        else:
            analysis['summary']['total_score'] = 0.0
        
        return analysis
    
    # ========================================================================
    # ZAMAN SERİSİ ANALİZİ İÇİN YARDIMCI FONKSİYON
    # ========================================================================
    
    @staticmethod
    def compare_analyses(previous: Dict, current: Dict) -> Dict:
        """
        İki analiz sonucunu karşılaştır
        
        Args:
            previous: Önceki analiz JSON
            current: Güncel analiz JSON
        
        Returns:
            Delta ve trend bilgisi
        """
        comparison = {
            'total_score_delta': 0,
            'trend': 'stable',
            'degraded_eyes': [],
            'improved_eyes': []
        }
        
        # Genel skor karşılaştırması
        prev_score = previous.get('summary', {}).get('total_score', 0)
        curr_score = current.get('summary', {}).get('total_score', 0)
        delta = curr_score - prev_score
        
        comparison['total_score_delta'] = round(delta, 2)
        
        if delta > 5:
            comparison['trend'] = 'improving'
        elif delta < -5:
            comparison['trend'] = 'degrading'
        
        # Göz bazlı karşılaştırma
        prev_eyes = {eye['eye_id']: eye for eye in previous.get('eyes', [])}
        curr_eyes = {eye['eye_id']: eye for eye in current.get('eyes', [])}
        
        for eye_id in curr_eyes:
            if eye_id in prev_eyes:
                prev_eye_score = prev_eyes[eye_id].get('hybrid_score', 0)
                curr_eye_score = curr_eyes[eye_id].get('hybrid_score', 0)
                eye_delta = curr_eye_score - prev_eye_score
                
                if eye_delta < -10:
                    comparison['degraded_eyes'].append({
                        'eye_id': eye_id,
                        'eye_name': curr_eyes[eye_id]['eye_name'],
                        'delta': round(eye_delta, 2)
                    })
                elif eye_delta > 10:
                    comparison['improved_eyes'].append({
                        'eye_id': eye_id,
                        'eye_name': curr_eyes[eye_id]['eye_name'],
                        'delta': round(eye_delta, 2)
                    })
        
        return comparison