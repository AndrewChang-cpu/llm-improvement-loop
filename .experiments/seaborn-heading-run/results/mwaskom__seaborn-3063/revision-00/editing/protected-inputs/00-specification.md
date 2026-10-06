Add Perc stat for computing percentiles

```python
(
    so.Plot(tips, "day", "total_bill")
    .add(so.Dot(), so.Perc(11))
    .add(so.Range(linewidth=3), so.Perc([10, 90]), so.Shift(x=.1))
)
```
<img width=500 src="https://user-images.githubusercontent.com/315810/194721740-2d8b2849-49d6-4d12-9c6f-c94e95246e9b.png" />
