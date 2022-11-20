from sympy import Point, Polygon

p1, p2, p3 = [(0.12233, 0.12442365), (1.65432, 0.09876543), (5.123456, 1.987654)]

print(float(Polygon(p1,p2,p3).area))