from geopy.distance import geodesic
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import logging
from typing import Optional, Tuple, Dict, Any

class LocationService:
    def __init__(self):
        self.geolocator = Nominatim(user_agent="kaamconnect")
        self.logger = logging.getLogger(__name__)
    
    def get_coordinates(self, address: str) -> Optional[Tuple[float, float]]:
        """
        Get latitude and longitude for a given address
        
        Args:
            address (str): The address to geocode
            
        Returns:
            Optional[Tuple[float, float]]: (latitude, longitude) if found, None otherwise
        """
        try:
            location = self.geolocator.geocode(address)
            if location:
                return (location.latitude, location.longitude)
            return None
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            self.logger.error(f"Geocoding error for address {address}: {str(e)}")
            return None
    
    def get_address(self, latitude: float, longitude: float) -> Optional[Dict[str, Any]]:
        """
        Get address details from coordinates
        
        Args:
            latitude (float): Latitude coordinate
            longitude (float): Longitude coordinate
            
        Returns:
            Optional[Dict]: Address components if found, None otherwise
        """
        try:
            location = self.geolocator.reverse(f"{latitude}, {longitude}", exactly_one=True)
            if location:
                return location.raw.get('address', {})
            return None
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            self.logger.error(f"Reverse geocoding error for ({latitude}, {longitude}): {str(e)}")
            return None
    
    def calculate_distance(
        self, 
        coord1: Tuple[float, float], 
        coord2: Tuple[float, float],
        unit: str = 'km'
    ) -> Optional[float]:
        """
        Calculate distance between two coordinates
        
        Args:
            coord1 (Tuple[float, float]): (latitude, longitude) of first point
            coord2 (Tuple[float, float]): (latitude, longitude) of second point
            unit (str): 'km' for kilometers, 'miles' for miles
            
        Returns:
            Optional[float]: Distance in specified unit, or None if calculation fails
        """
        try:
            distance = geodesic(coord1, coord2).kilometers
            if unit.lower() == 'miles':
                return distance * 0.621371  # Convert km to miles
            return distance
        except Exception as e:
            self.logger.error(f"Distance calculation error: {str(e)}")
            return None
    
    def get_nearby_jobs(
        self, 
        latitude: float, 
        longitude: float, 
        radius_km: float = 10.0,
        limit: int = 20
    ) -> list:
        """
        Find jobs within a certain radius of given coordinates
        
        Args:
            latitude (float): Center point latitude
            longitude (float): Center point longitude
            radius_km (float): Search radius in kilometers
            limit (int): Maximum number of results to return
            
        Returns:
            list: List of nearby jobs with distance information
        """
        from app import db
        from app.models import Job
        from sqlalchemy import func, text
        
        try:
            # Convert radius from km to degrees (approximate)
            radius_deg = radius_km / 111.0
            
            # Calculate bounding box for initial filtering
            lat_min = latitude - radius_deg
            lat_max = latitude + radius_deg
            lng_min = longitude - (radius_deg / abs(cos(radians(latitude))))
            lng_max = longitude + (radius_deg / abs(cos(radians(latitude))))
            
            # First filter by bounding box for performance
            nearby_jobs = Job.query.filter(
                Job.status == 'open',
                Job.latitude.between(lat_min, lat_max),
                Job.longitude.between(lng_min, lng_max)
            ).all()
            
            # Calculate exact distances and filter by radius
            results = []
            for job in nearby_jobs:
                if job.latitude and job.longitude:
                    distance = self.calculate_distance(
                        (latitude, longitude),
                        (job.latitude, job.longitude)
                    )
                    
                    if distance is not None and distance <= radius_km:
                        job_dict = job.to_dict()
                        job_dict['distance_km'] = distance
                        results.append(job_dict)
            
            # Sort by distance and limit results
            results.sort(key=lambda x: x['distance_km'])
            return results[:limit]
            
        except Exception as e:
            self.logger.error(f"Error finding nearby jobs: {str(e)}")
            return []

# Helper functions
def radians(degrees):
    """Convert degrees to radians"""
    from math import pi
    return degrees * (pi / 180)

def cos(radians):
    """Cosine function that works with degrees"""
    from math import cos as math_cos
    return math_cos(radians)

# Global instance
location_service = LocationService()
