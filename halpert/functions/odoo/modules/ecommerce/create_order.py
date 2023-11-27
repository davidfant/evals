import arrow
from halpert import Function
from pydantic import BaseModel, Field
from typing import List
from ...api import OdooAPI

class Address(BaseModel):
  street: str
  city: str
  zip: str

class Input(BaseModel):
  class LineItem(BaseModel):
    product_id: int
    quantity: int

  customer_id: int
  line_items: List[LineItem]


class Output(BaseModel):
  order_id: int


async def create_order_call(input: Input) -> Output:
  odoo = OdooAPI()
  # see command[1] here: https://github.com/odoo/odoo/blob/20ddb74a8aefbde137f5c47a769f26ec8a4f7113/odoo/fields.py#L4186
  ref = f'virtual_{round(arrow.utcnow().timestamp())}'
  record = odoo.create(
    'sale.order',
    {
      'order_line': [
        [OdooAPI.Command.CREATE.value, ref, {
          'name': f'Product {li.product_id}',
          'product_id': li.product_id,
          'product_uom_qty': li.quantity,
        }]
        for li in input.line_items
      ],
      'partner_id': input.customer_id,
      'state': 'sale',
    },
    ['id'],
  )

  return Output(order_id=record['id'])


create_order = Function(
  name='Create Order',
  description='Create order in Odoo eCommerce',
  icon='http://localhost:8069/website_sale/static/description/icon.png',
  Input=Input,
  Output=Output,
  call=create_order_call,
)

