from halpert import Function
from pydantic import BaseModel, Field
from typing import List
from ...api import OdooAPI

class Address(BaseModel):
  street: str
  city: str
  zip: str

class Input(BaseModel):
  Address = Address

  name: str
  address: Address | None


class Output(BaseModel):
  class Customer(BaseModel):
    id: int
    name: str
    address: Address | None
  
  customer: Customer


async def create_customer_call(input: Input) -> Output:
  odoo = OdooAPI()
  record = odoo.create(
    'res.partner',
    {
      'name': input.name,
      'street': input.address.street if input.address else False,
      'city': input.address.city if input.address else False,
      'zip': input.address.zip if input.address else False,
    },
    ['id', 'name', 'street', 'city', 'zip'],
  )

  return Output(customer=Output.Customer(
    id=record['id'],
    name=record['name'],
    address=Address(
      street=record['street'] or '',
      city=record['city'] or '',
      zip=record['zip'] or '',
    ) if record['street'] and record['city'] and record['zip'] else None,
  ))


create_customer = Function(
  name='Create Customer',
  description='Create customer in Odoo eCommerce',
  icon='http://localhost:8069/website_sale/static/description/icon.png',
  Input=Input,
  Output=Output,
  call=create_customer_call,
)

