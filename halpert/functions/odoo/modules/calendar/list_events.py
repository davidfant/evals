import arrow
from halpert import Function
from pydantic import BaseModel, Field
from typing import List
from .types import Event
from ...api import OdooAPI


class Input(BaseModel):
  start_date: str = Field(format='YYYY-MM-DD')
  end_date: str = Field(format='YYYY-MM-DD')


class Output(BaseModel):
  events: List[Event]


async def list_events_call(input: Input) -> Output:
  odoo = OdooAPI()
  results = odoo.search_read(
    'calendar.event',
    ['id', 'display_name', 'description', 'start', 'stop', 'partner_ids', 'allday'],
    [
      OdooAPI.SearchFilter(field='start', op='>=', value=input.start_date),
      OdooAPI.SearchFilter(field='stop', op='<', value=input.end_date),
    ]
  )

  return Output(events=[Event.from_api(e, odoo) for e in results])


list_events = Function(
  name='List Calendar Events',
  description='List events in Odoo Calendar',
  icon='http://localhost:8069/calendar/static/description/icon.png',
  Input=Input,
  Output=Output,
  call=list_events_call,
)
