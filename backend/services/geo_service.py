import math
from typing import Tuple, Optional
from backend.models.site import Site

class GeoService:
    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate Haversine distance between two points in meters.
        """
        R = 6371000  # Radius of Earth in meters
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)

        a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c

    def verify_location(self, lat: float, lon: float, site: Site) -> Tuple[bool, float]:
        """
        Check if user is within the site's radius.
        Returns: (is_inside, distance_in_meters)
        """
        distance = self.calculate_distance(lat, lon, site.latitude, site.longitude)
        is_inside = distance <= site.radius_meters
        return is_inside, distance

geo_service = GeoService()
