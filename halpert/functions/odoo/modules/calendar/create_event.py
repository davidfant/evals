import arrow
from halpert import Function
from pydantic import BaseModel, Field
from typing import List
from .types import Event
from ...api import OdooAPI


class Input(BaseModel):
  name: str
  description: str
  attendee_ids: List[int]
  start_date: str = Field(format='YYYY-MM-DD or YYYY-MM-DD HH:mm')
  end_date: str = Field(format='YYYY-MM-DD or YYYY-MM-DD HH:mm')


class Output(BaseModel):
  event: Event


async def create_event_call(input: Input) -> Output:
  odoo = OdooAPI()
  event = odoo.create(
    'calendar.event',
    {
      'name': input.name,
      'description': input.description,
      'partner_ids': [[OdooAPI.Command.LINK.value, id] for id in input.attendee_ids],
      'start': input.start_date,
      'stop': input.end_date,
    },
    ['id', 'display_name', 'description', 'start', 'stop', 'partner_ids', 'allday'],
  )

  return Output(event=Event.from_api(event, odoo))


create_event = Function(
  name='Create Calendar Event',
  description='Create and event in Odoo Calendar',
  icon='http://localhost:8069/calendar/static/description/icon.png',
  Input=Input,
  Output=Output,
  call=create_event_call,
)
