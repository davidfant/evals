from halpert import Function
from pydantic import BaseModel, Field
from typing import List
from ...api import OdooAPI


class Input(BaseModel):
  query: str


class Output(BaseModel):
  class Product(BaseModel):
    id: int
    name: str
    price: int
    available: bool

  products: List[Product]


async def search_products_call(input: Input) -> Output:
  odoo = OdooAPI()
  results = odoo.search_read(
    'product.template',
    ['name', 'list_price', 'qty_available'],
    [
      OdooAPI.SearchFilter(field='type', op='=', value='product'),
      OdooAPI.SearchFilter(field='name', op='ilike', value=input.query),
    ],
  )

  import json
  print(json.dumps(results, indent=2))

  return Output(products=[
    Output.Product(
      id=product['id'],
      name=product['name'],
      price=product['list_price'],
      available=bool(product['qty_available']),
    )
    for product in results
  ])


search_products = Function(
  name='Search Products',
  description='Search products by name',
  icon='http://localhost:8069/point_of_sale/static/description/icon.png',
  Input=Input,
  Output=Output,
  call=search_products_call,
)

