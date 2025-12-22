import cv2
import numpy as np
from sklearn.cluster import KMeans


class ColorAnalyzer:
    def __init__(self, n_colors: int = 5):
        self.n_colors = n_colors
    
    def extract_dominant_colors(self, image_path: str):
        """Extract dominant colors from image"""
        try:
            image = cv2.imread(image_path)
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Reshape image to be a list of pixels
            pixels = image.reshape(-1, 3)
            
            # Use KMeans to find dominant colors
            kmeans = KMeans(n_clusters=self.n_colors, random_state=42, n_init=10)
            kmeans.fit(pixels)
            
            # Get colors and percentages
            colors = kmeans.cluster_centers_.astype(int)
            labels = kmeans.labels_
            counts = np.bincount(labels)
            percentages = (counts / len(labels)) * 100
            
            # Sort by percentage
            sorted_indices = np.argsort(percentages)[::-1]
            
            dominant_colors = []
            for idx in sorted_indices:
                color = colors[idx].tolist()
                hex_color = '#{:02x}{:02x}{:02x}'.format(color[0], color[1], color[2])
                dominant_colors.append({
                    'rgb': color,
                    'hex': hex_color,
                    'percentage': round(float(percentages[idx]), 2)
                })
            
            return {
                'success': True,
                'colors': dominant_colors
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def compare_colors(self, color1: list, color2: list):
        """Compare two RGB colors using Euclidean distance"""
        color1 = np.array(color1)
        color2 = np.array(color2)
        distance = np.linalg.norm(color1 - color2)
        
        # Normalize to 0-100 similarity score
        max_distance = np.sqrt(3 * (255 ** 2))
        similarity = (1 - (distance / max_distance)) * 100
        
        return round(similarity, 2)
    
    def analyze_product_colors(self, image_path: str, bbox: list, reference_colors: dict):
        """Analyze colors in specific product region"""
        try:
            image = cv2.imread(image_path)
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Crop to bbox
            x1, y1, x2, y2 = map(int, bbox)
            product_region = image[y1:y2, x1:x2]
            
            # Get dominant colors
            pixels = product_region.reshape(-1, 3)
            kmeans = KMeans(n_clusters=min(3, len(pixels)), random_state=42, n_init=10)
            kmeans.fit(pixels)
            dominant = kmeans.cluster_centers_.astype(int)[0].tolist()
            
            # Compare with reference colors
            color_match_scores = {}
            for color_name, hex_color in reference_colors.items():
                # Convert hex to RGB
                hex_color = hex_color.lstrip('#')
                ref_rgb = [int(hex_color[i:i+2], 16) for i in (0, 2, 4)]
                
                # Calculate similarity
                similarity = self.compare_colors(dominant, ref_rgb)
                color_match_scores[color_name] = similarity
            
            return {
                'success': True,
                'dominant_color': dominant,
                'color_match_scores': color_match_scores,
                'best_match': max(color_match_scores.items(), key=lambda x: x[1])[0] if color_match_scores else None
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
