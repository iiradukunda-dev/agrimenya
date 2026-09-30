from app.ml import predict

# Example input (Gasabo / Maize / Season A)
result = predict.predict_yield(
    district="Gasabo",
    crop="Maize",
    season="A",
    rainfall_mm=800,
    area_cultivated=0.5,
    household_size=4,
)
print("predict_yield ->", result)

pred_total, conf, ver = result
priority = predict.classify_priority(pred_total, 0.5)
print("classification ->", priority)
