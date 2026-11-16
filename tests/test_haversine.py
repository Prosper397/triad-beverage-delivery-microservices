import pytest

from common.haversine import distance_km


def test_distance_nulle():
    assert distance_km(6.1319, 1.2228, 6.1319, 1.2228) == 0.0


def test_distance_un_degre_de_longitude_a_l_equateur():
    # 1 degré de longitude à l'équateur ≈ 111,195 km
    assert distance_km(0.0, 0.0, 0.0, 1.0) == pytest.approx(111.1949, rel=1e-4)


def test_distance_paris_londres():
    # Distance Haversine connue : Paris ↔ Londres ≈ 343,5 km
    assert distance_km(48.8566, 2.3522, 51.5074, -0.1278) == pytest.approx(343.5, abs=1.0)
