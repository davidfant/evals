from halpert import Function
from pydantic import BaseModel, Field
from typing import List
from ...api import OdooAPI


class Input(BaseModel):
  query: str | None = None


class Output(BaseModel):
  class Product(BaseModel):
    id: int
    name: str
    description: str
    price: int
    available: bool

  products: List[Product]


async def search_products_call(input: Input) -> Output:
  odoo = OdooAPI()
  filters = [
    OdooAPI.SearchFilter(field='type', op='in', value=['product', 'consu']),
    OdooAPI.SearchFilter(field='is_published', op='=', value=True),
  ]
  if input.query:
    filters.append(OdooAPI.SearchFilter(field='name', op='ilike', value=input.query))
  results = odoo.search_read(
    'product.template',
    ['name', 'description', 'list_price', 'purchase_ok'],
    filters,
  )

  return Output(products=[
    Output.Product(
      id=product['id'],
      name=product['name'],
      description=product['description'] or '',
      price=product['list_price'],
      available=bool(product['purchase_ok']),
    )
    for product in results
  ])


search_products = Function(
  name='Search Products',
  description='Search products by name',
  icon='http://localhost:8069/website_sale/static/description/icon.png',
  Input=Input,
  Output=Output,
  call=search_products_call,
)

