from app.ml import predict


def test_predict_returns_tuple():
    total, conf, ver = predict.predict_yield(
        district=None, crop="Maize", season=None, rainfall_mm=None, area_cultivated=0.5, household_size=4
    )
    assert isinstance(total, float)
    assert 0.0 <= conf <= 1.0
    assert isinstance(ver, str)
