"""
This is a DeltaV compatible agent responsible for finding a nearby restaurant based on a location given by the user.
"""

from uagents import Agent, Model, Context, Protocol
import uuid
from typing import Optional
from ai_engine import KeyValue

# modules from booking_protocol.py
from booking_protocol import UAgentResponse, UAgentResponseType, booking_proto

# placeholder for a function that can retrieve real up-to-date restaurant data
from restaurant_info import PRAGUE_RESTAURANT

agent = Agent()

restaurant_protocol = Protocol("Restaurants")

class Restaurant(Model):
    latitude: float
    longitude: float
    miles_radius: float
    additional_amenities: Optional[str]
    cuisine_type: Optional[str]


removed_items = ["undefined", "unknown", "none", "null", ""]
def filter_restaurants(data, miles_radius, amenities, cuisine):
    """Function to filters restaurant data based on specified criteria"""
    response = [restaurant for restaurant in data if (not miles_radius or restaurant["distance"] <= miles_radius) and (amenities.lower() in removed_items or restaurant["additional_amenities"].lower() == amenities.lower()) and (cuisine.lower() in removed_items or restaurant["cuisine_type"].lower() == cuisine.lower())]
    return response


def get_data(miles_radius, amenities, cuisine) -> list or None:
    """Function to retrieve restaurant data based on specified criteria."""
    if amenities == None:
        amenities = ""
    if cuisine == None:
        cuisine = ""
    return filter_restaurants(PRAGUE_RESTAURANT, miles_radius, amenities, cuisine)


@restaurant_protocol.on_message(model=Restaurant, replies=UAgentResponse)
async def on_message(ctx: Context, sender: str, msg: Restaurant):
    """Handles restaurant requests and responds with a list of nearby options"""
    ctx.logger.info(f"Received message from {sender}.")
    try:
        data = get_data(msg.miles_radius, msg.additional_amenities, msg.cuisine_type)
        request_id = str(uuid.uuid4())
        options = []
        ctx_storage = {}
        for idx, o in enumerate(data):
            option = f"""● This is Restaurant: {o['name']} which is located {o['distance']} miles away from location
● Additional amenity is {o["additional_amenities"]}
● Cuisine type is {o["cuisine_type"]}"""
            options.append(KeyValue(key=idx, value=option))
            ctx_storage[idx] = option
        ctx.storage.set(request_id, ctx_storage)
        if options:
            await ctx.send(sender,
                           UAgentResponse(options=options, type=UAgentResponseType.SELECT_FROM_OPTIONS,
                                          request_id=request_id))
        else:
            await ctx.send(sender,
                           UAgentResponse(message="No restaurant are available for this context",
                                          type=UAgentResponseType.FINAL,
                                          request_id=request_id))

    except Exception as exc:
        ctx.logger.error(exc)
        await ctx.send(sender, UAgentResponse(message=str(exc), type=UAgentResponseType.ERROR))

# Include protocols in agent
agent.include(restaurant_protocol)
agent.include(booking_proto)

if __name__ == "__main__":
    agent.run()
    
    
