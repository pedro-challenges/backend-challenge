"""Defines Rental class: constructed from input json
Defines load_hook that takes input json and output computed price/commissions.
"""
from datetime import datetime

cfg = {
    "commission_base": 0.3,  # Commission base 30%
    "insurance_commission_part": 0.5,  # Half goes to the insurance
    "assistance_fee_per_day": 100  # Assistance fee 1 EUR/day
}


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

        # Empty commission dict, compute_commission() initializes it
        self.commission = {}

    def get_discount_multiplier(self):
        """Compute discount multiplier based on rental duration."""
        # 1st day no discount
        multiplier = 1
        # From day 2 to 4, 10% discount
        if self.duration > 1:
            multiplier = multiplier + \
                (self.duration - 1) * \
                0.9 if self.duration < 4 else multiplier + 3 * 0.9
        # From day 5 to 10, 30% discount
        if self.duration > 4:
            multiplier = multiplier + \
                (self.duration - 4) * \
                0.7 if self.duration < 10 else multiplier + 6 * 0.7
        # From day 11, 50% discount
        if self.duration > 10:
            multiplier = multiplier + (self.duration - 10) * 0.5
        return multiplier

    def compute_price(self, car):
        """Compute price."""
        if self.duration <= 0 or self.distance < 0 or \
                car.get('price_per_day', 0) < 0 or \
                car.get('price_per_km', 0) < 0:
            raise NegativePrice

        day_price = self.get_discount_multiplier() * car.get('price_per_day', 0)
        distance_price = self.distance * car.get('price_per_km', 0)
        self.price = int(round(day_price + distance_price))

    def compute_commission(self):
        """Compute each actor's commission."""
        self.commission = {
            'insurance_fee': int(round(
                self.price * cfg['commission_base']
                * cfg['insurance_commission_part'])),
            'assistance_fee': int(round(
                self.duration * cfg['assistance_fee_per_day'])),
            'drivy_fee': int(round(
                self.price * cfg['commission_base'] *
                (1 - cfg['insurance_commission_part'])
                - self.duration * cfg['assistance_fee_per_day']))
        }

    def compute_costs(self, car):
        """compute rental's price and commissions."""
        self.compute_price(car)
        self.compute_commission()

    def get_dict(self):
        """Return output dictionary."""
        return {
            'id': self.id,
            'price': self.price,
            'commission': self.commission
        }


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
                rental.compute_costs(cars[rental.car_id])
            except KeyError:
                # If car is missing to compute rental: print/log on backend.
                # On output.json price will be 0 and commission empty and can be
                # handled by input.json provider.
                # TBD: add metadata to communicate exceptions.
                print("Missing car id %d to compute rental id %d." %
                      (rental.car_id, rental.id))
            except NegativePrice:
                # If a component of price is negative: print/log on backend.
                # On output.json price will be 0 and commission empty and can be
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
