import cv2
import numpy as np
from typing import List, Tuple
import os

class ImageEnhancer:
    def enhance(self, image_path: str, out_path: str = None) -> dict:
        img = cv2.imread(image_path)
        if img is None:
            raise FileNotFoundError(image_path)
        # Simple enhancement: histogram equalization for color images
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        l2 = cv2.equalizeHist(l)
        lab = cv2.merge((l2, a, b))
        enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        out_path = out_path or image_path.replace(".", "_enh.")
        cv2.imwrite(out_path, enhanced)
        # placeholder tags (could add CLIP/ViT-CLIP)
        tags = self._simple_color_tags(enhanced)
        return {"enhanced_path": out_path, "tags": tags}

    def _simple_color_tags(self, img) -> List[str]:
        # very basic color detection
        avg = img.mean(axis=(0,1))
        tags = []
        b,g,r = avg
        if r > g and r > b:
            tags.append("warm")
        elif b > r and b > g:
            tags.append("cool")
        else:
            tags.append("neutral")
        return tags
