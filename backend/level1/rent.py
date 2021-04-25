"""Defines Rental class: constructed from input json
Defines load_hook that takes input json and output computed price.
"""
from datetime import datetime


class NegativePrice(Exception):
    """NegativePrice class for exceptions"""
    pass


class Rental:
    """Class representing a Rental entry."""

    def __init__(self, json_data):
        """Construct object from loaded json."""
        self.id = json_data['id']
        self.car_id = json_data['car_id']
        self.distance = json_data['distance']

        # Compute rental duration in days
        self.start_date = datetime.strptime(
            json_data['start_date'], '%Y-%m-%d')
        self.end_date = datetime.strptime(json_data['end_date'], '%Y-%m-%d')
        self.duration = (self.end_date - self.start_date).days + 1

        self.price = 0

    def compute_price(self, car):
        """Compute price."""
        if self.duration <= 0 or self.distance < 0 or \
                car.get('price_per_day', 0) < 0 or \
                car.get('price_per_km', 0) < 0:
            raise NegativePrice

        day_price = self.duration * car.get('price_per_day', 0)
        distance_price = self.distance * car.get('price_per_km', 0)
        self.price = int(round(day_price + distance_price))

    def get_dict(self):
        """Return output dictionary."""
        return {'id': self.id, 'price': self.price}


def load_hook(dct):
    """Hook called when loading json."""
    # Check if it's the main dict and run data processing
    if "cars" in dct:
        # Cars dict to select car from ID
        cars = {car.get("id"): car for car in dct['cars']}
        # Rentals list
        rentals = dct['rentals']
        # Compute price for every rental
        for rental in rentals:
            try:
                rental.compute_price(cars[rental.car_id])
            except KeyError:
                # If car is missing to compute rental: print/log on backend.
                # On output.json price will be 0 and can be handled by
                # input.json provider.
                # TBD: add metadata to communicate exceptions.
                print("Missing car id %d to compute rental id %d." %
                      (rental.car_id, rental.id))
            except NegativePrice:
                # If a component of price is negative: print/log on backend.
                # On output.json price will be 0 and can be
                # handled by input.json provider.
                # TBD: add metadata to communicate exceptions.
                print("Negative price component on rental id %d." % rental.id)

        # Create rentals list with desired output
        return {'rentals': [rental.get_dict() for rental in rentals]}

    # Check if it's one of the rentals dict and return a rental object
    if "car_id" in dct:
        return Rental(dct)

    # Default return dict without further processing
    return dct
