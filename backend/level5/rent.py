"""Defines Rental class: constructed from input json
Defines load_hook that takes input json and output computed price and actions.
"""
from datetime import datetime

cfg = {
    "commission_base": 0.3,  # Commission base 30%
    "insurance_commission_part": 0.5,  # Half goes to the insurance
    "assistance_fee_per_day": 100,  # Assistance fee 1 EUR/day
    "options_prices": {  # Additional features prices per day (in EUR cents)
        "gps": {
            "owner_fee": 500  # GPS: 5€/day, all the money goes to the owner
        },
        "baby_seat": {
            "owner_fee": 200  # Baby Seat: 2€/day, all the money to the owner
        },
        "additional_insurance": {
            "drivy_fee": 1000  # Additional Insurance: 10€/day, all to Getaround
        }
    }
}


class NegativePrice(Exception):
    """NegativePrice class for exceptions"""
    pass


class OptionNotFound(Exception):
    """OptionNotFound class for exceptions: if additional feature is not
    configured"""

    def __init__(self, option_id, name):
        self.option_id = option_id
        self.name = name

    # Error message
    def __str__(self):
        return "Option id %d with name %s not found." % \
            (self.option_id, self.name)


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

        # Rental additional features list
        self.options = []

        # Base price: excluding additional features
        self.base_price = 0

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
        self.base_price = int(round(day_price + distance_price))
        self.price = self.base_price + self.get_options_total_price()

    def compute_commission(self):
        """Compute each actor's commission."""
        options_price = self.get_options_price()
        self.commission = {
            # Level 4: Add owner to commission so it iterates on get_actions()
            'owner_fee': int(round(
                self.base_price * (1 - cfg['commission_base'])))
            + options_price.get('owner_fee', 0) * self.duration,
            'insurance_fee': int(round(
                self.base_price * cfg['commission_base']
                * cfg['insurance_commission_part'])),
            'assistance_fee': int(round(
                self.duration * cfg['assistance_fee_per_day'])),
            'drivy_fee': int(round(
                self.base_price * cfg['commission_base'] *
                (1 - cfg['insurance_commission_part'])
                - self.duration * cfg['assistance_fee_per_day']))
            + options_price.get('drivy_fee', 0) * self.duration
        }

    def compute_costs(self, car):
        """compute rental's price and commissions."""
        self.compute_price(car)
        self.compute_commission()

    def get_actions(self):
        """Return actions: how much money must be
        debited/credited for each actor."""
        # Initialize list with total price debit to driver
        rental_actions = [
            {
                "who": "driver",
                "type": "debit",
                "amount": self.price
            }]

        # Iterate commission list and append credit action for each actor.
        # Remove "_fee" from the end of the string to respect desired "who" name
        for key in self.commission:
            rental_actions.append({
                "who": key.replace('_fee', ''),
                "type": "credit",
                "amount": self.commission[key]
            })
        return rental_actions

    def add_option(self, option):
        """Add additional feature to the rental."""
        self.options.append(option)

    def get_options_price(self):
        """Return additional features price dict with price for each actor."""
        options_price = {
            "owner_fee": 0,
            "drivy_fee": 0
        }

        for option in self.options:
            try:
                options_price = {
                    key: options_price.get(key, 0)
                    + cfg['options_prices'].get(option['type']).get(key, 0)
                    for key in options_price
                }
            except AttributeError as option_not_configured:
                raise OptionNotFound(option['id'], option['type']) \
                    from option_not_configured

        return options_price

    def get_options_total_price(self):
        """Return total price for all additional features."""
        return sum(self.get_options_price().values()) * self.duration

    def get_dict(self):
        """Return output dictionary."""
        return {
            'id': self.id,
            "options": [option['type'] for option in self.options],
            'actions': self.get_actions()
        }


def load_hook(dct):
    """Hook called when loading json."""
    # Check if it's the main dict and run data processing
    if "cars" in dct:
        # Cars dict to select from ID
        cars = {car.get("id"): car for car in dct['cars']}
        # Rentals dict to select from ID
        rentals = {rental.id: rental for rental in dct['rentals']}
        # Iterate over additional features list and add it to rental.
        missing_rentals = []
        for option in dct['options']:
            try:
                rentals[option['rental_id']].add_option(option)
            except KeyError:
                # If rental is missing to add option: print/log on backend.
                # missing_rentals will be added to output.json and can be
                # handled by input.json provider.
                print("Missing rental id %d to compute option id %d." %
                      (option['rental_id'], option['id']))
                missing_rentals.append({
                    'rental_id': option['rental_id'],
                    'option_id': option['id']})
        # Compute price for every rental
        for rental in rentals.values():
            try:
                rental.compute_costs(cars[rental.car_id])
            except KeyError:
                # If car is missing to compute rental: print/log on backend.
                # On output.json driver debit cost will be 0 and can be
                # handled by input.json provider.
                # TBD: add metadata to communicate exceptions.
                print("Missing car id %d to compute rental id %d." %
                      (rental.car_id, rental.id))
            except NegativePrice:
                # If a component of price is negative: print/log on backend.
                # On output.json driver debit cost will be 0 and can be
                # handled by input.json provider.
                # TBD: add metadata to communicate exceptions.
                print("Negative price component on rental id %d." % rental.id)
            except OptionNotFound as error_msg:
                # If an option is not configured print/log on backend.
                # On output.json driver debit cost will be 0 and can be
                # handled by input.json provider.
                # TBD: add metadata to communicate exceptions.
                print(error_msg)

        result = {'rentals': [rental.get_dict()
                              for rental in rentals.values()]}

        if missing_rentals:
            result['missing_rentals'] = missing_rentals

        # Create rentals list with desired output
        return result

    # Check if it's one of the rentals dict and return a rental object
    if "car_id" in dct:
        return Rental(dct)

    # Default return dict without further processing
    return dct
