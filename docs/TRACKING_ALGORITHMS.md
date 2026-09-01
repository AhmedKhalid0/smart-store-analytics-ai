# Multi-Object Tracking & Spatial Geometry Algorithms

Author: Ahmed Khaled (Ahmed Algendy)  
Email: contact@ahmedalgendy.com  
GitHub: [https://github.com/AhmedKhalid0](https://github.com/AhmedKhalid0)  
Website: [https://ahmedalgendy.com](https://ahmedalgendy.com)  

---

## 1. Centroid & IoU Association Matrix

The tracking engine correlates detected person bounding boxes across consecutive video frames:
1. **Centroid Distance Cost**:
   $$D_{\text{Euclid}}(C_i, C_j) = \sqrt{(x_i - x_j)^2 + (y_i - y_j)^2}$$
2. **Intersection over Union (IoU)**:
   $$\text{IoU}(A, B) = \frac{\text{Area}(A \cap B)}{\text{Area}(A \cup B)}$$
3. **Hungarian Bipartite Matching**: Minimizes total assignment cost while terminating lost tracks after $M=30$ missed frames.
