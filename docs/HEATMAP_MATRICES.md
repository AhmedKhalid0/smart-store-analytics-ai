# Spatial Heatmap Generation & Kernel Density Estimation

Author: Ahmed Khaled (Ahmed Algendy)  
Email: contact@ahmedalgendy.com  
GitHub: [https://github.com/AhmedKhalid0](https://github.com/AhmedKhalid0)  
Website: [https://ahmedalgendy.com](https://ahmedalgendy.com)  

---

## 1. 2D Gaussian Kernel Splatting

Customer trajectory coordinates $(x_t, y_t)$ accumulate into a spatial density grid $M \in \mathbb{R}^{W \times H}$:

$$G(x, y) = \exp\left(-\frac{(x - x_t)^2 + (y - y_t)^2}{2\sigma^2}\right)$$

* **Decay Factor**: Configurable temporal decay $\alpha = 0.98$ for moving averages.
* **Color Mapping**: Normalizes density values to Turbo/Inferno colormaps for clear visualization of hot merchandise displays.
